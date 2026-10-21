import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import ssl
import csv
import io
import json
import re
import os
import time
import typing
from core.data_manager import data_manager
from cogs.admin import is_admin_or_role

# -----------------------------------------------------------
#  Supported Countries & Open Data Sources (No API keys needed)
# -----------------------------------------------------------

SUPPORTED_COUNTRIES = {
    "vn": {
        "name": "🇻🇳 Vietnam",
        "flag": "🇻🇳",
        "label": "Vietnam",
        "currency": "VND",
        "description": "Petrolimex official retail fuel prices",
        "source_name": "petrolimex.com.vn",
        "source_url": "https://petrolimex.com.vn/",
        "aliases": ["vn", "vietnam", "viet nam"],
    },
    "us": {
        "name": "🇺🇸 United States",
        "flag": "🇺🇸",
        "label": "United States",
        "currency": "USD/gal",
        "description": "AAA national daily retail averages",
        "source_name": "gasprices.aaa.com (AAA)",
        "source_url": "https://gasprices.aaa.com/",
        "aliases": ["us", "usa", "united states", "america"],
    },
    "uk": {
        "name": "🇬🇧 United Kingdom",
        "flag": "🇬🇧",
        "label": "United Kingdom",
        "currency": "pence/L",
        "description": "DESNZ / GOV.UK weekly pump averages",
        "source_name": "gov.uk / DESNZ",
        "source_url": "https://www.gov.uk/government/statistical-data-sets/oil-and-petroleum-products-weekly-statistics",
        "aliases": ["uk", "gb", "great britain", "united kingdom", "england"],
    },
    "jp": {
        "name": "🇯🇵 Japan",
        "flag": "🇯🇵",
        "label": "Japan",
        "currency": "JPY/L",
        "description": "e-nenpi nationwide fuel price survey",
        "source_name": "e-nenpi.com",
        "source_url": "https://e-nenpi.com/",
        "aliases": ["jp", "japan", "jpn", "nihon", "nippon"],
    },
    "fr": {
        "name": "🇫🇷 France",
        "flag": "🇫🇷",
        "label": "France",
        "currency": "EUR/L",
        "description": "data.economie.gouv.fr live nationwide averages",
        "source_name": "data.economie.gouv.fr",
        "source_url": "https://data.economie.gouv.fr/explore/dataset/prix-des-carburants-en-france-flux-instantane-v2/",
        "aliases": ["fr", "france"],
    },
    "tw": {
        "name": "🇹🇼 Taiwan",
        "flag": "🇹🇼",
        "label": "Taiwan",
        "currency": "TWD/L",
        "description": "CPC Taiwan (台灣中油) retail fuel prices",
        "source_name": "cpc.com.tw (CPC)",
        "source_url": "https://www.cpc.com.tw/",
        "aliases": ["tw", "taiwan"],
    },
}

def resolve_country(query: typing.Optional[str]) -> typing.Optional[str]:
    """Resolves a user-provided string or code to a supported country code."""
    if not query:
        return None
    q = query.strip().lower()
    for code, info in SUPPORTED_COUNTRIES.items():
        if q == code or q in info.get("aliases", []):
            return code
    return None

# Autocomplete helper for slash commands
async def country_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    current_lower = current.lower().strip()
    choices = []
    for code, info in SUPPORTED_COUNTRIES.items():
        display_name = f"{info['flag']} {info['label']} ({code.upper()})"
        if (
            not current_lower
            or current_lower in code
            or current_lower in info["label"].lower()
            or any(current_lower in a for a in info.get("aliases", []))
        ):
            choices.append(app_commands.Choice(name=display_name, value=code))
    return choices[:25]


# -----------------------------------------------------------
#  Scrapers / Open Data Fetchers (Zero API keys required)
# -----------------------------------------------------------

async def fetch_vietnam(session: aiohttp.ClientSession) -> list:
    """Fetches Vietnam Petrolimex retail prices (open search API)."""
    url = (
        "https://portals.petrolimex.com.vn/~apis/portals/cms.item/search"
        "?object-identity=search"
        "&x-request=eyJGaWx0ZXJCeSI6eyJBbmQiOlt7IlN5c3RlbUlEIjp7IkVxdWFscyI6IjY3"
        "ODNkYzEyNzFmZjQ0OWU5NWI3NGE5NTIwOTY0MTY5In19LHsiUmVwb3NpdG9yeUlEIjp7IkVx"
        "dWFscyI6ImE5NTQ1MWUyM2I0NzRmZTU4ODZiZmI3Y2Y4NDNmNTNjIn19LHsiUmVwb3NpdG9y"
        "eUVudGl0eUlEIjp7IkVxdWFscyI6IjM4MDEzNzhmZTFlMDQ1YjFhZmExMGRlN2M1Nzc2MTI0"
        "In19LHsiU3RhdHVzIjp7IkVxdWFscyI6IlB1Ymxpc2hlZCJ9fV19LCJTb3J0QnkiOnsiTGFz"
        "dE1vZGlmaWVkIjoiRGVzY2VuZGluZyJ9LCJQYWdpbmF0aW9uIjp7IlRvdGFsUmVjb3JkcyI6"
        "LTEsIlRvdGFsUGFnZXMiOjAsIlBhZ2VTaXplIjowLCJQYWdlTnVtYmVyIjowfX0="
    )
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.petrolimex.com.vn",
        "Referer": "https://www.petrolimex.com.vn/",
    }
    timeout = aiohttp.ClientTimeout(total=10)
    async with session.get(url, headers=headers, timeout=timeout) as resp:
        if resp.status != 200:
            raise ValueError(f"HTTP {resp.status} from Petrolimex")
        data = await resp.json()

    def fmt_vnd(p):
        s = str(int(p))
        return (s[:-3] + "." + s[-3:]) if len(s) > 3 else s

    results = []
    for item in data.get("Objects", []):
        title = item.get("Title", "")
        z1 = item.get("Zone1Price", 0)
        z2 = item.get("Zone2Price", 0)
        if title and z1 > 0:
            if "Xăng" in title:
                emoji = "🚗"
            elif "DO" in title:
                emoji = "🚚"
            elif "hỏa" in title:
                emoji = "🔥"
            elif "Mazut" in title:
                emoji = "⛴️"
            else:
                emoji = "💧"
            results.append({
                "label": f"{emoji} {title}",
                "value": f"🟢 Vùng 1: **{fmt_vnd(z1)} đ**\n🟡 Vùng 2: **{fmt_vnd(z2)} đ**",
            })
    return results


async def fetch_us(session: aiohttp.ClientSession) -> list:
    """Fetches US nationwide retail fuel prices from AAA Gas Prices."""
    url = "https://gasprices.aaa.com/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    timeout = aiohttp.ClientTimeout(total=10)
    async with session.get(url, headers=headers, timeout=timeout) as resp:
        if resp.status != 200:
            raise ValueError(f"HTTP {resp.status} from AAA")
        html = await resp.text()

    match = re.search(r'<table[^>]*>(.*?)</table>', html, re.DOTALL | re.IGNORECASE)
    if not match:
        raise ValueError("Could not find price table on AAA Gas Prices")

    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', match.group(1), re.DOTALL | re.IGNORECASE)
    headers_row = []
    current_avg_row = []
    yesterday_avg_row = []

    for row in rows:
        cols = [re.sub(r'<[^>]+>', '', c).strip() for c in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL | re.IGNORECASE)]
        if any("Regular" in c for c in cols):
            headers_row = cols
        elif any("Current Avg." in c for c in cols):
            current_avg_row = cols
        elif any("Yesterday Avg." in c for c in cols):
            yesterday_avg_row = cols

    fuel_emojis = {
        "Regular": "🚗",
        "Mid-Grade": "🔹",
        "Premium": "💎",
        "Diesel": "🚚",
        "E85": "🌿",
    }

    results = []
    for i, h in enumerate(headers_row[1:], start=1):
        emoji = fuel_emojis.get(h, "⛽")
        curr = current_avg_row[i] if i < len(current_avg_row) else "N/A"
        yest = yesterday_avg_row[i] if i < len(yesterday_avg_row) else ""
        yest_note = f" _(Yesterday: {yest})_" if yest else ""
        results.append({
            "label": f"{emoji} {h}",
            "value": f"**{curr} / gal**{yest_note}",
        })
    return results


async def fetch_uk(session: aiohttp.ClientSession) -> list:
    """Fetches UK weekly pump prices from DESNZ / GOV.UK open dataset."""
    landing_url = "https://www.gov.uk/government/statistical-data-sets/oil-and-petroleum-products-weekly-statistics"
    csv_url = "https://assets.publishing.service.gov.uk/media/6acd0403ec9d3aba1e013c7b/CSV__2018_-__.csv"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    try:
        async with session.get(landing_url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as r:
            if r.status == 200:
                html = await r.text()
                m = re.search(r'href="([^"]+CSV[^"]+\.csv)"', html, re.I)
                if m:
                    csv_url = m.group(1)
    except Exception:
        pass

    timeout = aiohttp.ClientTimeout(total=10)
    async with session.get(csv_url, headers=headers, timeout=timeout) as resp:
        if resp.status != 200:
            raise ValueError(f"HTTP {resp.status} from GOV.UK CSV")
        text = await resp.text(encoding="utf-8-sig", errors="replace")

    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    last_row = None
    for row in rows[1:]:
        if len(row) >= 3 and row[0].strip() and row[1].strip():
            last_row = row

    results = []
    if last_row:
        date = last_row[0].strip()
        try:
            ulsp = float(last_row[1].strip())
            results.append({
                "label": "🚗 Unleaded Petrol (ULSP)",
                "value": f"**{ulsp:.1f}p / litre**  _(Week of {date})_",
            })
        except (ValueError, IndexError):
            pass
        try:
            ulsd = float(last_row[2].strip())
            results.append({
                "label": "🚚 Diesel (ULSD)",
                "value": f"**{ulsd:.1f}p / litre**  _(Week of {date})_",
            })
        except (ValueError, IndexError):
            pass
    return results


async def fetch_japan(session: aiohttp.ClientSession) -> list:
    """Fetches Japan nationwide retail fuel survey from e-nenpi."""
    url = "https://e-nenpi.com/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    timeout = aiohttp.ClientTimeout(total=10)
    async with session.get(url, headers=headers, timeout=timeout) as resp:
        if resp.status != 200:
            raise ValueError(f"HTTP {resp.status} from e-nenpi")
        html = await resp.text()

    idx = html.find("今日のガソリン価格")
    if idx == -1:
        raise ValueError("Could not find gasoline price block on e-nenpi")
    block = html[idx:idx + 2500]

    update_match = re.search(r'UPDATE\s+([0-9/:\s]+)', block)
    update_str = f" _({update_match.group(0).strip()})_" if update_match else ""

    fuels = [
        ("レギュラー", "🚗 Regular (レギュラー)"),
        ("ハイオク", "💎 High-Octane (ハイオク)"),
        ("軽油", "🚚 Diesel (軽油)"),
    ]
    results = []
    for term, label in fuels:
        pos = block.find(term)
        if pos != -1:
            snippet = block[pos:pos + 350]
            digits = re.findall(r'<span[^>]*class="num[0-9]"[^>]*>([0-9])</span>', snippet)
            has_dot = "." in re.sub(r'<[^>]+>', '', snippet)
            if digits:
                if has_dot and len(digits) >= 2:
                    price_str = "".join(digits[:-1]) + "." + digits[-1]
                else:
                    price_str = "".join(digits)
                results.append({
                    "label": label,
                    "value": f"**¥{price_str} / litre**{update_str}",
                })
    return results


async def fetch_france(session: aiohttp.ClientSession) -> list:
    """Fetches France live nationwide fuel averages from data.economie.gouv.fr."""
    url = (
        "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/"
        "prix-des-carburants-en-france-flux-instantane-v2/records"
        "?select=avg(gazole_prix)%20as%20gazole,%20avg(sp95_prix)%20as%20sp95,%20"
        "avg(sp98_prix)%20as%20sp98,%20avg(e10_prix)%20as%20e10,%20avg(e85_prix)%20as%20e85,%20avg(gplc_prix)%20as%20gplc"
        "&limit=1"
    )
    headers = {"User-Agent": "Mozilla/5.0"}
    timeout = aiohttp.ClientTimeout(total=10)
    async with session.get(url, headers=headers, timeout=timeout) as resp:
        if resp.status != 200:
            raise ValueError(f"HTTP {resp.status} from data.economie.gouv.fr")
        data = await resp.json()

    total_count = data.get("total_count", 0)
    count_note = f" _(~{total_count:,} stations live)_" if total_count else ""
    row = (data.get("results") or [{}])[0]

    fuel_labels = [
        ("gazole", "🚚 Gazole / Diesel"),
        ("sp95", "🚗 SP95"),
        ("sp98", "💎 SP98"),
        ("e10", "🌿 E10 (SP95-E10)"),
        ("e85", "🌽 E85"),
        ("gplc", "💨 GPLc"),
    ]
    results = []
    for key, label in fuel_labels:
        val = row.get(key)
        if val is not None and val > 0:
            results.append({
                "label": label,
                "value": f"**€{val:.3f} / litre**{count_note}",
            })
    return results


async def fetch_taiwan(session: aiohttp.ClientSession) -> list:
    """Fetches Taiwan official retail prices from CPC Taiwan (台灣中油)."""
    url = "https://www.cpc.com.tw/GetOilPriceJson.aspx?type=TodayOilPriceString"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    timeout = aiohttp.ClientTimeout(total=10)

    async with session.get(url, headers=headers, ssl=ssl_context, timeout=timeout) as resp:
        if resp.status != 200:
            raise ValueError(f"HTTP {resp.status} from CPC Taiwan")
        text = await resp.text()
        data = json.loads(text)

    date_str = data.get("PriceUpdate", "")
    note = f" _(Updated: {date_str})_" if date_str else ""

    items = [
        ("sPrice1", "🚗 92 無鉛汽油 (92 Unleaded)", "L"),
        ("sPrice2", "🔹 95 無鉛汽油 (95 Unleaded)", "L"),
        ("sPrice3", "💎 98 無鉛汽油 (98 Unleaded)", "L"),
        ("sPrice5", "🚚 超級柴油 (Super Diesel)", "L"),
        ("sPrice4", "🌿 酒精汽油 (Ethanol Petrol)", "L"),
        ("sPrice6", "💨 液化石油氣 (LPG)", "kg"),
    ]
    results = []
    for key, label, unit in items:
        val = data.get(key)
        if val:
            results.append({
                "label": label,
                "value": f"**NT$ {val} / {unit}**{note}",
            })
    return results


FETCHERS = {
    "vn": fetch_vietnam,
    "us": fetch_us,
    "uk": fetch_uk,
    "jp": fetch_japan,
    "fr": fetch_france,
    "tw": fetch_taiwan,
}


# -----------------------------------------------------------
#  Interactive Country Select View
# -----------------------------------------------------------

class CountrySelectView(discord.ui.View):
    """Dropdown menu for selecting a default country for the server."""

    def __init__(self, author: discord.User, current_country: typing.Optional[str] = None):
        super().__init__(timeout=60)
        self.author = author
        self.chosen_code: typing.Optional[str] = None

        options = []
        for code, info in SUPPORTED_COUNTRIES.items():
            is_default = (code == current_country)
            options.append(
                discord.SelectOption(
                    label=info["label"],
                    value=code,
                    emoji=info["flag"],
                    description=info["description"][:50],
                    default=is_default,
                )
            )

        self.select_menu = discord.ui.Select(
            placeholder="Choose default country for this server...",
            options=options,
            min_values=1,
            max_values=1,
        )
        self.select_menu.callback = self.select_callback
        self.add_item(self.select_menu)

    async def select_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(
                "❌ Only the person who ran the command can choose the country.",
                ephemeral=True,
            )

        self.chosen_code = self.select_menu.values[0]
        info = SUPPORTED_COUNTRIES.get(self.chosen_code, {})
        await interaction.response.edit_message(
            content=f"⏳ Configured default country to **{info.get('name', self.chosen_code)}**! Fetching prices...",
            view=None,
        )
        self.stop()


# -----------------------------------------------------------
#  Embed Builder
# -----------------------------------------------------------

def build_price_embed(country_code: str, items: list, is_temporary_override: bool = False, server_default_name: typing.Optional[str] = None) -> discord.Embed:
    info = SUPPORTED_COUNTRIES[country_code]
    title_suffix = f" — {info['name']}"
    if is_temporary_override:
        title_suffix += " (Lookup)"

    embed = discord.Embed(
        title=f"⛽ Fuel Prices{title_suffix}",
        description=f"_{info['description']}_\n",
        color=discord.Color.brand_green(),
        url=info.get("source_url"),
        timestamp=discord.utils.utcnow(),
    )
    for item in items:
        embed.add_field(name=item["label"], value=item["value"], inline=False)

    footer_parts = [f"Source: {info.get('source_name')}"]
    if is_temporary_override and server_default_name:
        footer_parts.append(f"Server default: {server_default_name} (run without args for default)")
    else:
        footer_parts.append("Change server default: /gasconfig")

    embed.set_footer(text=" • ".join(footer_parts))
    return embed


# -----------------------------------------------------------
#  Cog Implementation
# -----------------------------------------------------------

class GasPrice(commands.Cog):
    CACHE_TTL_SECONDS = 1800  # 30-minute in-memory cache to prevent repeated scraping

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._price_cache: dict[str, dict] = {}

    async def _get_prices(self, country_code: str) -> list:
        """Retrieves prices with an in-memory TTL cache to ensure instant responses."""
        now = time.time()
        cached = self._price_cache.get(country_code)
        if cached and (now - cached["timestamp"] < self.CACHE_TTL_SECONDS):
            return cached["items"]

        fetcher = FETCHERS.get(country_code)
        if not fetcher:
            raise ValueError(f"Unsupported country code: {country_code}")

        async with aiohttp.ClientSession() as session:
            items = await fetcher(session)

        if items:
            self._price_cache[country_code] = {
                "timestamp": now,
                "items": items,
            }
        return items

    async def _fetch_and_respond(
        self,
        ctx: commands.Context,
        country_code: str,
        is_temporary_override: bool = False,
        server_default_name: typing.Optional[str] = None,
        target_message: typing.Optional[discord.Message] = None,
    ):
        try:
            items = await self._get_prices(country_code)
        except Exception as e:
            info = SUPPORTED_COUNTRIES.get(country_code, {})
            err_text = f"❌ Failed to fetch gas prices for **{info.get('name', country_code)}**:\n> `{e}`"
            if target_message:
                return await target_message.edit(content=err_text, view=None)
            return await ctx.send(err_text)

        if not items:
            no_data_text = f"⚠️ No price data found right now for **{country_code.upper()}**."
            if target_message:
                return await target_message.edit(content=no_data_text, view=None)
            return await ctx.send(no_data_text)

        embed = build_price_embed(
            country_code,
            items,
            is_temporary_override=is_temporary_override,
            server_default_name=server_default_name,
        )

        file = None
        if os.path.exists("assets/images/gas_banner.gif"):
            file = discord.File("assets/images/gas_banner.gif", filename="gas_banner.gif")
            embed.set_image(url="attachment://gas_banner.gif")

        if target_message:
            try:
                if file:
                    await target_message.edit(content=None, embed=embed, attachments=[file], view=None)
                else:
                    await target_message.edit(content=None, embed=embed, view=None)
                return
            except Exception:
                pass

        if file:
            await ctx.send(embed=embed, file=file)
        else:
            await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="gas",
        description="Show current fuel prices. In a new server, asks for country config on first run.",
    )
    @commands.guild_only()
    @app_commands.guild_only()
    @app_commands.describe(country="Optional: country code or name to look up without changing server default (e.g. jp, us, vn)")
    async def get_gas_price(self, ctx: commands.Context, *, country: typing.Optional[str] = None):
        if not ctx.guild:
            return await ctx.send("❌ This command can only be used inside a server.", ephemeral=True)

        config = await data_manager.get_server_config(ctx.guild.id)
        default_country = config.get("gas_country")

        # CASE 1: User explicitly provided a country code/name (Temporary override - does NOT change config)
        if country:
            resolved = resolve_country(country)
            if not resolved:
                valid_list = ", ".join(f"`{k.upper()}` ({v['name']})" for k, v in SUPPORTED_COUNTRIES.items())
                return await ctx.send(
                    f"❌ Unknown country `{country}`.\n"
                    f"Supported countries: {valid_list}\n"
                    f"Example: `{ctx.prefix}gas jp` or `{ctx.prefix}gas us`",
                    ephemeral=True,
                )

            await ctx.defer()
            default_info = SUPPORTED_COUNTRIES.get(default_country)
            default_name = default_info["name"] if default_info else None
            is_override = (resolved != default_country)
            await self._fetch_and_respond(
                ctx,
                resolved,
                is_temporary_override=is_override,
                server_default_name=default_name,
            )
            return

        # CASE 2: No country provided, but server has a saved default country
        if default_country and default_country in SUPPORTED_COUNTRIES:
            await ctx.defer()
            await self._fetch_and_respond(ctx, default_country)
            return

        # CASE 3: First-time run: server has no country configured yet
        view = CountrySelectView(author=ctx.author)
        setup_text = (
            "⛽ **Fuel Price Setup**\n"
            "This server doesn't have a default country configured for fuel prices yet.\n"
            "Please select a country below to set the server's default (Admins can change this later with `/gasconfig`):"
        )
        msg = await ctx.send(setup_text, view=view)
        await view.wait()

        if not view.chosen_code:
            try:
                await msg.edit(
                    content="⏱️ Setup timed out. Run `y!gas` again to configure.",
                    view=None,
                )
            except Exception:
                pass
            return

        chosen = view.chosen_code
        await data_manager.set_server_config(ctx.guild.id, "gas_country", chosen)
        await self._fetch_and_respond(ctx, chosen, target_message=msg)

    @get_gas_price.autocomplete("country")
    async def gas_country_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        return await country_autocomplete(interaction, current)

    @commands.hybrid_command(
        name="gasconfig",
        description="(Admin) Set or change this server's default country for fuel prices.",
    )
    @commands.guild_only()
    @app_commands.guild_only()
    @app_commands.describe(country="Optional: set default country directly (e.g. jp, us, vn, uk, fr, tw)")
    @commands.check(is_admin_or_role)
    async def gas_config(self, ctx: commands.Context, *, country: typing.Optional[str] = None):
        if not ctx.guild:
            return await ctx.send("❌ This command can only be used inside a server.", ephemeral=True)

        config = await data_manager.get_server_config(ctx.guild.id)
        current = config.get("gas_country")

        # If admin supplied a country argument
        if country:
            resolved = resolve_country(country)
            if not resolved:
                valid_list = ", ".join(f"`{k.upper()}` ({v['name']})" for k, v in SUPPORTED_COUNTRIES.items())
                return await ctx.send(
                    f"❌ Unknown country `{country}`.\nSupported countries: {valid_list}",
                    ephemeral=True,
                )
            await data_manager.set_server_config(ctx.guild.id, "gas_country", resolved)
            info = SUPPORTED_COUNTRIES[resolved]
            return await ctx.send(
                f"✅ Default fuel price country updated to **{info['name']}**!\n"
                f"Members can now run `{ctx.prefix}gas` to see prices for {info['label']}.",
            )

        # Otherwise, show interactive dropdown
        current_name = SUPPORTED_COUNTRIES.get(current, {}).get("name", "Not set yet")
        view = CountrySelectView(author=ctx.author, current_country=current)
        msg = await ctx.send(
            f"⚙️ **Server Gas Price Configuration**\n"
            f"Current default: **{current_name}**\n\n"
            "Select a new default country for this server below:",
            view=view,
            ephemeral=True,
        )
        await view.wait()

        if not view.chosen_code:
            try:
                await msg.edit(content="⏱️ Configuration timed out. No changes were made.", view=None)
            except Exception:
                pass
            return

        chosen = view.chosen_code
        await data_manager.set_server_config(ctx.guild.id, "gas_country", chosen)
        info = SUPPORTED_COUNTRIES[chosen]
        try:
            await msg.edit(
                content=f"✅ Default fuel price country successfully updated to **{info['name']}**!",
                view=None,
            )
        except Exception:
            await ctx.send(
                f"✅ Default fuel price country successfully updated to **{info['name']}**!",
                ephemeral=True,
            )

    @gas_config.autocomplete("country")
    async def gasconfig_country_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        return await country_autocomplete(interaction, current)


async def setup(bot: commands.Bot):
    await bot.add_cog(GasPrice(bot))
