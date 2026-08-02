import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import os
import re
import asyncio
from core.data_manager import data_manager

ANILIST_API_URL = "https://graphql.anilist.co"

USER_ADV_QUERY = """
query ($userId: Int!) {
  followers: Page(perPage: 1) { pageInfo { total } followers(userId: $userId) { id } }
  following: Page(perPage: 1) { pageInfo { total } following(userId: $userId) { id } }
  
  topAnime: Page(perPage: 3) { 
    mediaList(userId: $userId, type: ANIME, sort: [SCORE_DESC, UPDATED_TIME_DESC], status: COMPLETED) { 
      score 
      media { title { english romaji } } 
    } 
  }
  topManga: Page(perPage: 3) { 
    mediaList(userId: $userId, type: MANGA, sort: [SCORE_DESC, UPDATED_TIME_DESC], status: COMPLETED) { 
      score 
      media { title { english romaji } } 
    } 
  }
}
"""

# GraphQL Queries
MEDIA_QUERY = """
query ($search: String, $id: Int, $type: MediaType) {
  Media(search: $search, id: $id, type: $type) {
    id
    title {
      english
      romaji
    }
    coverImage {
      large
    }
    description(asHtml: false)
    studios(isMain: true) {
      nodes {
        name
      }
    }
    staff {
      edges {
        role
        node {
          name {
            full
          }
        }
      }
    }
    format
    episodes
    chapters
    startDate {
      year
      month
      day
    }
    averageScore
    tags {
      name
      rank
    }
    relations {
      edges {
        relationType
        node {
          title {
            english
            romaji
          }
        }
      }
    }
    mediaListEntry {
      status
      progress
      score
    }
  }
}
"""

CHARACTER_QUERY = """
query ($search: String, $id: Int) {
  Character(search: $search, id: $id) {
    id
    name {
      full
      native
      userPreferred
    }
    image {
      large
    }
    gender
    age
    description(asHtml: false)
    favourites
  }
}
"""

STAFF_QUERY = """
query ($search: String, $id: Int) {
  Staff(search: $search, id: $id) {
    id
    name {
      full
      native
      userPreferred
    }
    image {
      large
    }
    gender
    description(asHtml: false)
    favourites
  }
}
"""

MASTER_SEARCH_QUERY = """
query ($search: String) {
  anime: Page(perPage: 10) { media(search: $search, type: ANIME) { id, title { english, romaji } } }
  manga: Page(perPage: 10) { media(search: $search, type: MANGA) { id, title { english, romaji } } }
  characters: Page(perPage: 10) { characters(search: $search) { id, name { full, native } } }
  staff: Page(perPage: 10) { staff(search: $search) { id, name { full, native } } }
  users: Page(perPage: 10) { users(search: $search) { id, name } }
}
"""

USER_QUERY = """
query ($id: Int, $name: String) {
  User(id: $id, name: $name) {
    id
    name
    about(asHtml: false)
    avatar { large }
    siteUrl
    updatedAt
    statistics {
      anime {
        count
        minutesWatched
        meanScore
        genres(limit: 5, sort: COUNT_DESC) { genre }
      }
      manga {
        count
        chaptersRead
        meanScore
      }
    }
  }
}
"""

VIEWER_QUERY = """
query {
  Viewer {
    id
    name
    about(asHtml: false)
    avatar { large }
    siteUrl
    updatedAt
    statistics {
      anime {
        count
        minutesWatched
        meanScore
        genres(limit: 5, sort: COUNT_DESC) { genre }
      }
      manga {
        count
        chaptersRead
        meanScore
      }
    }
  }
}
"""

class AniListAPIError(Exception):
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message
        super().__init__(f"API Error {status_code}: {message}")

class AniListSearchView(discord.ui.View):
    def __init__(self, cog, interaction, search_data, query):
        super().__init__(timeout=300)
        self.cog = cog
        self.original_interaction = interaction
        self.search_data = search_data
        self.query = query
        self.current_category = "anime"
        self.update_components()

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item):
        if isinstance(error, AniListAPIError):
            file = discord.File("assets/images/api_down.jpg")
            content = f"**Error {error.status_code}**: {error.message}"
            try:
                if interaction.response.is_done(): await interaction.followup.send(content=content, file=file)
                else: await interaction.response.send_message(content=content, file=file)
            except Exception: pass

    def update_components(self):
        self.clear_items()
        
        for cat, label, emoji in [("anime", "Anime", "📺"), ("manga", "Manga", "📖"), ("characters", "Characters", "👤"), ("staff", "Staff", "🎭"), ("users", "Users", "👥")]:
            style = discord.ButtonStyle.primary if self.current_category == cat else discord.ButtonStyle.secondary
            btn = discord.ui.Button(label=label, emoji=emoji, style=style, custom_id=f"cat_{cat}")
            btn.callback = self.make_category_callback(cat)
            self.add_item(btn)
            
        options = []
        items = self.search_data.get(self.current_category, {}).get("media" if self.current_category in ["anime", "manga"] else self.current_category, [])
        for item in items[:25]:
            if self.current_category in ["anime", "manga"]:
                title = item["title"]["english"] or item["title"]["romaji"]
            elif self.current_category == "users":
                title = item["name"]
            else:
                title = item["name"]["full"]
            options.append(discord.SelectOption(label=title[:100], value=str(item["id"])))
            
        if not options:
            options.append(discord.SelectOption(label="No results found.", value="none"))
            
        select = discord.ui.Select(placeholder="Select a result...", options=options, disabled=len(options)==0 or options[0].value=="none", row=1)
        select.callback = self.select_callback
        self.add_item(select)

    def generate_embed(self):
        desc = "Select a category and choose a result from the dropdown below.\n\n"
        items = self.search_data.get(self.current_category, {}).get("media" if self.current_category in ["anime", "manga"] else self.current_category, [])
        
        for i, item in enumerate(items[:10], 1):
            if self.current_category in ["anime", "manga"]:
                title = item["title"]["english"] or item["title"]["romaji"]
            elif self.current_category == "users":
                title = item["name"]
            else:
                title = item["name"]["full"]
            desc += f"**{i}.** {title}\n"
            
        if not items:
            desc += "*No results found in this category.*"
            
        return discord.Embed(title=f"Search Results for '{self.query}'", description=desc, color=0x02a9ff)

    def make_category_callback(self, category):
        async def callback(interaction: discord.Interaction):
            self.current_category = category
            self.update_components()
            await interaction.response.edit_message(embed=self.generate_embed(), view=self)
        return callback

    async def select_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        item_id = interaction.data["values"][0]
        if item_id == "none": return
        
        embed = None
        if self.current_category == "anime":
            embed = await self.cog.build_media_embed(interaction.user.id, media_id=item_id, media_type="ANIME")
        elif self.current_category == "manga":
            embed = await self.cog.build_media_embed(interaction.user.id, media_id=item_id, media_type="MANGA")
        elif self.current_category == "characters":
            embed = await self.cog.build_character_embed(char_id=item_id)
        elif self.current_category == "staff":
            embed = await self.cog.build_staff_embed(staff_id=item_id)
        elif self.current_category == "users":
            embed, err = await self.cog.build_user_embed(user_id=item_id)
            if not embed:
                await interaction.followup.send(f"❌ {err}")
                return
            
        if embed:
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("❌ Failed to load details.")


class AniList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    anilist = app_commands.Group(name="anilist", description="AniList integration commands")

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        original = getattr(error, 'original', error)
        if isinstance(original, AniListAPIError):
            file = discord.File("assets/images/api_down.jpg")
            content = f"**Error {original.status_code}**: {original.message}"
            try:
                if interaction.response.is_done(): await interaction.followup.send(content=content, file=file)
                else: await interaction.response.send_message(content=content, file=file)
            except Exception: pass
            return

    async def _fetch_graphql(self, query: str, variables: dict, token: str = None):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(ANILIST_API_URL, json={"query": query, "variables": variables}, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if "errors" in data and not data.get("data"):
                            err_msg = data["errors"][0].get("message", "Unknown error")
                            status = data["errors"][0].get("status", 200)
                            raise AniListAPIError(status, err_msg)
                        return data.get("data")
                    elif resp.status == 404:
                        return None
                    else:
                        try:
                            data = await resp.json()
                            if "errors" in data and len(data["errors"]) > 0:
                                err_msg = data["errors"][0].get("message", "Unknown error")
                                status = data["errors"][0].get("status", resp.status)
                                raise AniListAPIError(status, err_msg)
                        except Exception as parse_err:
                            if isinstance(parse_err, AniListAPIError): raise
                        raise AniListAPIError(resp.status, "API is currently down or unresponsive.")
        except AniListAPIError:
            raise
        except Exception:
            raise AniListAPIError("Unknown", "Connection error")

    def clean_html(self, text):
        if not text:
            return "*No description available.*"
        text = re.sub(r'<br\s*/?>', '\n', text)
        text = re.sub(r'<[^>]+>', '', text)
        if len(text) > 250:
            return text[:247] + "..."
        return text

    async def build_media_embed(self, user_id: int, search: str = None, media_id = None, media_type: str = None):
        user_data = await data_manager.get_user_data(user_id)
        token = user_data.get("anilist_token")

        variables = {}
        if media_type: variables["type"] = media_type
        if media_id: variables["id"] = int(media_id)
        elif search: variables["search"] = search
        else: return None

        data = await self._fetch_graphql(MEDIA_QUERY, variables, token)
        if not data or not data.get("Media"): return None

        media = data["Media"]
        title_en = media["title"]["english"] or media["title"]["romaji"]
        title_romaji = media["title"]["romaji"]
        mtype = media_type or media.get("type", "ANIME")
        url = f"https://anilist.co/{mtype.lower()}/{media['id']}"
        
        embed = discord.Embed(
            title=f"{title_en}",
            url=url,
            color=0x02a9ff if mtype == "ANIME" else 0xe85d75
        )
        
        # Use img.anili.st for media covers as requested
        embed.set_image(url=f"https://img.anili.st/media/{media['id']}")
            
        desc = self.clean_html(media["description"])
        embed.description = f"**{title_romaji}**\n\n{desc}"
        
        if mtype == "ANIME":
            studios = [s["name"] for s in media["studios"]["nodes"]]
            if studios:
                embed.add_field(name="🎬 Studio", value=", ".join(studios), inline=True)
        else:
            authors = []
            for edge in media["staff"]["edges"]:
                role = edge["role"].lower()
                if "story" in role or "art" in role or "original creator" in role:
                    authors.append(edge["node"]["name"]["full"])
            if authors:
                embed.add_field(name="✍️ Author", value=", ".join(set(authors)), inline=True)

        fmt = media.get("format", "Unknown").replace("_", " ") if media.get("format") else "Unknown"
        length = f"{media.get('episodes', '?')} Eps" if mtype == "ANIME" else f"{media.get('chapters', '?')} Chp"
        embed.add_field(name="📺 Format", value=f"{fmt} ({length})", inline=True)
        
        sd = media.get("startDate", {})
        date_str = "Unknown"
        if sd.get("year"):
            date_str = f"{sd.get('year')}-{sd.get('month', '01'):02d}-{sd.get('day', '01'):02d}"
        embed.add_field(name="🗓️ Release Date", value=date_str, inline=True)
        
        score = media.get("averageScore")
        embed.add_field(name="⭐ Score", value=f"{score}%" if score else "N/A", inline=True)
        
        tags = media.get("tags", [])
        tags = sorted(tags, key=lambda t: t.get("rank", 0), reverse=True)[:4]
        if tags:
            embed.add_field(name="🏷️ Tags", value=", ".join(t["name"] for t in tags), inline=False)
            
        relations = []
        for edge in media.get("relations", {}).get("edges", []):
            rel_type = edge["relationType"].replace("_", " ").title()
            if rel_type in ["Source", "Prequel", "Sequel", "Alternative"]:
                rel_title = edge["node"]["title"]["english"] or edge["node"]["title"]["romaji"]
                relations.append(f"**{rel_type}**: {rel_title}")
        if relations:
            embed.add_field(name="🔗 Relations", value="\n".join(relations[:3]), inline=False)

        if media.get("mediaListEntry"):
            entry = media["mediaListEntry"]
            status = entry.get("status", "UNKNOWN").replace("_", " ").title()
            progress = entry.get("progress", 0)
            user_score = entry.get("score")
            score_str = str(user_score) if user_score else "*Not Rated*"
            embed.add_field(name="👤 Your Status", value=f"**{status}** - {progress} {length.split()[1].lower()} - ⭐ {score_str}", inline=False)

        return embed

    async def build_character_embed(self, search: str = None, char_id = None):
        variables = {}
        if char_id: variables["id"] = int(char_id)
        elif search: variables["search"] = search
        else: return None
        
        data = await self._fetch_graphql(CHARACTER_QUERY, variables)
        if not data or not data.get("Character"): return None
            
        char = data["Character"]
        url = f"https://anilist.co/character/{char['id']}"
        embed = discord.Embed(url=url, color=0x66cda8)
        
        name = char["name"]
        en_name = name.get("full") or name.get("userPreferred") or "Unknown"
        jp_name = name.get("native") or ""
        embed.title = f"👤 {en_name} {f'({jp_name})' if jp_name else ''}"
        
        if char["image"]["large"]:
            embed.set_image(url=char["image"]["large"])
            
        embed.description = self.clean_html(char["description"])
        embed.add_field(name="🚻 Gender", value=char.get("gender") or "Unknown", inline=True)
        if char.get("age"):
            embed.add_field(name="🎂 Age/Height", value=char.get("age")[:100], inline=True)
        embed.add_field(name="❤️ Favourites", value=f"{char.get('favourites', 0):,}", inline=True)
        
        return embed

    async def build_staff_embed(self, search: str = None, staff_id = None):
        variables = {}
        if staff_id: variables["id"] = int(staff_id)
        elif search: variables["search"] = search
        else: return None
        
        data = await self._fetch_graphql(STAFF_QUERY, variables)
        if not data or not data.get("Staff"): return None
            
        staff = data["Staff"]
        url = f"https://anilist.co/staff/{staff['id']}"
        embed = discord.Embed(url=url, color=0xb47bde)
        
        name = staff["name"]
        en_name = name.get("full") or name.get("userPreferred") or "Unknown"
        jp_name = name.get("native") or ""
        embed.title = f"🎭 {en_name} {f'({jp_name})' if jp_name else ''}"
        
        if staff["image"]["large"]:
            embed.set_image(url=staff["image"]["large"])
            
        embed.description = self.clean_html(staff["description"])
        embed.add_field(name="🚻 Gender", value=staff.get("gender") or "Unknown", inline=True)
        embed.add_field(name="❤️ Favourites", value=f"{staff.get('favourites', 0):,}", inline=True)
        
        return embed


    async def build_user_embed(self, user_id=None, username=None, discord_user_id=None):
        variables = {}
        token = None
        query = USER_QUERY

        if discord_user_id:
            user_data = await data_manager.get_user_data(discord_user_id)
            token = user_data.get("anilist_token")
            if not token:
                return None, "This user has not linked their AniList account."
            query = VIEWER_QUERY
        else:
            if user_id: variables["id"] = int(user_id)
            elif username: variables["name"] = username
            else: return None, "No user specified."
            
        try:
            data = await self._fetch_graphql(query, variables, token)
        except AniListAPIError:
            raise
        except Exception as e:
            return None, f"AniList API Error: {e}"

        if not data:
            return None, "User not found or profile is private."
            
        user = data.get("User") or data.get("Viewer")
        if not user:
            return None, "User not found or profile is private."

        url = user.get("siteUrl", f"https://anilist.co/user/{user['id']}")
        embed = discord.Embed(title=user["name"], url=url, color=0x3db4f2)
        
        embed.set_image(url=f"https://img.anili.st/user/{user['id']}")
            
        desc = self.clean_html(user.get("about"))
        if desc and desc != "*No description available.*":
            embed.description = desc
            
        stats = user.get("statistics", {})
        anime_stats = stats.get("anime", {})
        manga_stats = stats.get("manga", {})

        # Fetch advanced stats
        adv_data = None
        try:
            adv_data = await self._fetch_graphql(USER_ADV_QUERY, {"userId": user["id"]})
        except Exception:
            pass

        followers = adv_data.get("followers", {}).get("pageInfo", {}).get("total", 0) if adv_data else 0
        following = adv_data.get("following", {}).get("pageInfo", {}).get("total", 0) if adv_data else 0
        embed.add_field(name="👥 Network", value=f"**Followers**: {followers:,} | **Following**: {following:,}", inline=False)

        # Anime Stats
        a_count = anime_stats.get("count", 0)
        a_days = round(anime_stats.get("minutesWatched", 0) / 60 / 24, 1) if anime_stats.get("minutesWatched") else 0
        a_score = anime_stats.get("meanScore", 0)
        embed.add_field(name="📺 Anime Stats", value=f"**Total**: {a_count:,}\n**Days Watched**: {a_days}\n**Mean Score**: {a_score}%", inline=True)

        # Manga Stats
        m_count = manga_stats.get("count", 0)
        m_chapters = manga_stats.get("chaptersRead", 0)
        m_score = manga_stats.get("meanScore", 0)
        embed.add_field(name="📖 Manga Stats", value=f"**Total**: {m_count:,}\n**Chapters Read**: {m_chapters:,}\n**Mean Score**: {m_score}%", inline=True)

        # Genres
        genres = anime_stats.get("genres", [])
        if genres:
            genre_list = ", ".join(g["genre"] for g in genres)
            embed.add_field(name="🏷️ Top Genres", value=genre_list, inline=False)
            
        if adv_data:
            top_a = adv_data.get("topAnime", {}).get("mediaList", [])
            if top_a:
                val = ""
                for entry in top_a:
                    title = entry["media"]["title"]["english"] or entry["media"]["title"]["romaji"]
                    score_str = f"⭐ {entry['score']}" if entry.get("score") else "*(Unrated)*"
                    val += f"• {title[:40]} - {score_str}\n"
                embed.add_field(name="🏆 Top Anime", value=val, inline=True)
                
            top_m = adv_data.get("topManga", {}).get("mediaList", [])
            if top_m:
                val = ""
                for entry in top_m:
                    title = entry["media"]["title"]["english"] or entry["media"]["title"]["romaji"]
                    score_str = f"⭐ {entry['score']}" if entry.get("score") else "*(Unrated)*"
                    val += f"• {title[:40]} - {score_str}\n"
                embed.add_field(name="📚 Top Manga", value=val, inline=True)

        # Last Activity
        if user.get("updatedAt"):
            import datetime
            dt = datetime.datetime.fromtimestamp(user["updatedAt"])
            embed.set_footer(text=f"Last Active: {dt.strftime('%Y-%m-%d %H:%M:%S')}")

        return embed, None


    @anilist.command(name="login", description="Link your AniList account to the bot.")
    async def al_login(self, interaction: discord.Interaction):
        user_data = await data_manager.get_user_data(interaction.user.id)
        if user_data.get("anilist_token"):
            await interaction.response.send_message("You are already logged in to AniList!", ephemeral=True)
            return
            
        client_id = os.getenv("ANILIST_CLIENT_ID")
        redirect_uri = os.getenv("ANILIST_REDIRECT_URI")
        
        if not client_id or not redirect_uri:
            await interaction.response.send_message("AniList integration is not fully configured. Please contact the bot admin.", ephemeral=True)
            return

        state = data_manager.encrypt_string(str(interaction.user.id))
        auth_url = f"https://anilist.co/api/v2/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&state={state}"
        
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Click to Link AniList Account", url=auth_url, style=discord.ButtonStyle.link))
        
        await interaction.response.send_message("Please click the button below to authorize the bot on AniList.", view=view, ephemeral=True)
        
        try:
            user_id, success = await self.bot.wait_for(
                'anilist_login', 
                check=lambda u, s: u == interaction.user.id, 
                timeout=300.0
            )
            if success:
                await interaction.edit_original_response(content="✅ **Your AniList account has been successfully linked!**", view=None)
            else:
                await interaction.edit_original_response(content="❌ **Failed to link your AniList account.**", view=None)
        except asyncio.TimeoutError:
            await interaction.edit_original_response(content="⏳ **Login timed out. Please try running the command again.**", view=None)

    @anilist.command(name="logout", description="Unlink your AniList account from the bot.")
    async def al_logout(self, interaction: discord.Interaction):
        user_data = await data_manager.get_user_data(interaction.user.id)
        if not user_data.get("anilist_token"):
            await interaction.response.send_message("You haven't logged in to AniList yet.", ephemeral=True)
            return
            
        await data_manager.remove_user_data(interaction.user.id, "anilist_token")
        await interaction.response.send_message("👋 Your AniList account has been unlinked.", ephemeral=True)

    @anilist.command(name="profile", description="View an AniList profile.")
    @app_commands.describe(user="Discord ping (@user), AniList username, ID, or profile URL")
    async def al_profile(self, interaction: discord.Interaction, user: str = None):
        await interaction.response.defer()
        
        embed = None
        error = None
        
        if user:
            user = user.strip()
            match = re.match(r'^<@!?(\d+)>$', user)
            url_match = re.search(r'anilist\.co/user/([^/]+)', user)
            
            if match:
                discord_id = int(match.group(1))
                embed, error = await self.build_user_embed(discord_user_id=discord_id)
            elif url_match:
                item_id = url_match.group(1)
                if item_id.isdigit():
                    embed, error = await self.build_user_embed(user_id=int(item_id))
                else:
                    embed, error = await self.build_user_embed(username=item_id)
            elif user.isdigit():
                embed, error = await self.build_user_embed(user_id=int(user))
            else:
                embed, error = await self.build_user_embed(username=user)
        else:
            embed, error = await self.build_user_embed(discord_user_id=interaction.user.id)
            
        if embed:
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(f"❌ {error}")

    @anilist.command(name="search", description="Search AniList across all categories, or paste a link.")
    async def search_all(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        
        # Check if URL
        match = re.search(r'anilist\.co/(anime|manga|character|staff|user)/([^/]+)', query.lower())
        if match:
            category, item_id = match.groups()
            embed = None
            if category == "anime": embed = await self.build_media_embed(interaction.user.id, media_id=item_id, media_type="ANIME")
            elif category == "manga": embed = await self.build_media_embed(interaction.user.id, media_id=item_id, media_type="MANGA")
            elif category == "character": embed = await self.build_character_embed(char_id=item_id)
            elif category == "staff": embed = await self.build_staff_embed(staff_id=item_id)
            elif category == "user":
                if item_id.isdigit(): embed, _ = await self.build_user_embed(user_id=int(item_id))
                else: embed, _ = await self.build_user_embed(username=item_id)
            
            if embed: await interaction.followup.send(embed=embed)
            else: await interaction.followup.send("❌ Invalid AniList link or data not found.")
            return

        # Fetch master search
        try:
            data = await self._fetch_graphql(MASTER_SEARCH_QUERY, {"search": query})
        except AniListAPIError:
            raise
        except Exception as e:
            await interaction.followup.send("❌ An error occurred while searching.")
            return

        if not data:
            await interaction.followup.send("❌ An error occurred while searching.")
            return
            
        view = AniListSearchView(self, interaction, data, query)
        embed = view.generate_embed()
        await interaction.followup.send(embed=embed, view=view)

    @anilist.command(name="anime", description="Search for an anime on AniList")
    async def search_anime(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        embed = await self.build_media_embed(interaction.user.id, search=query, media_type="ANIME")
        if embed: await interaction.followup.send(embed=embed)
        else: await interaction.followup.send(f"❌ Could not find any anime matching `{query}`.")

    @anilist.command(name="manga", description="Search for a manga on AniList")
    async def search_manga(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        embed = await self.build_media_embed(interaction.user.id, search=query, media_type="MANGA")
        if embed: await interaction.followup.send(embed=embed)
        else: await interaction.followup.send(f"❌ Could not find any manga matching `{query}`.")

    @anilist.command(name="character", description="Search for a character on AniList")
    async def search_character(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        embed = await self.build_character_embed(search=query)
        if embed: await interaction.followup.send(embed=embed)
        else: await interaction.followup.send(f"❌ Could not find any character matching `{query}`.")
        
    @anilist.command(name="staff", description="Search for a staff/author on AniList")
    async def search_staff(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        embed = await self.build_staff_embed(search=query)
        if embed: await interaction.followup.send(embed=embed)
        else: await interaction.followup.send(f"❌ Could not find any staff matching `{query}`.")

    @commands.Cog.listener()
    async def on_anilist_link_detected(self, message: discord.Message, category: str, item_id):
        try:
            embed = None
            if category == "anime": embed = await self.build_media_embed(message.author.id, media_id=item_id, media_type="ANIME")
            elif category == "manga": embed = await self.build_media_embed(message.author.id, media_id=item_id, media_type="MANGA")
            elif category == "character": embed = await self.build_character_embed(char_id=item_id)
            elif category == "staff": embed = await self.build_staff_embed(staff_id=item_id)
            elif category == "user":
                if str(item_id).isdigit():
                    embed, _ = await self.build_user_embed(user_id=int(item_id))
                else:
                    embed, _ = await self.build_user_embed(username=str(item_id))
            
            if embed:
                await message.reply(embed=embed, mention_author=False)
        except AniListAPIError as e:
            file = discord.File("assets/images/api_down.jpg")
            content = f"**Error {e.status_code}**: {e.message}"
            await message.reply(content=content, file=file, mention_author=False)

async def setup(bot):
    await bot.add_cog(AniList(bot))
