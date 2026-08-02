import discord
from discord import app_commands
from discord.ext import commands
import re
from urllib.parse import urlparse
import asyncio
from core.data_manager import data_manager
from cogs.admin import is_admin_or_role

URL_REGEX = r'(https?://[^\s]+)'

PLATFORM_MAP = {
    'twitter': {
        'domains': ['twitter.com', 'www.twitter.com', 'x.com', 'www.x.com'],
        'replace': 'fixupx.com'
    },
    'tiktok': {
        'domains': ['tiktok.com', 'www.tiktok.com', 'vm.tiktok.com', 'vt.tiktok.com'],
        'replace': 'tnktok.com'
    },
    'instagram': {
        'domains': ['instagram.com', 'www.instagram.com'],
        'replace': 'kkinstagram.com'
    },
    'facebook': {
        'domains': ['facebook.com', 'www.facebook.com', 'fb.watch', 'www.fb.watch'],
        'replace': 'facebed.com'
    },
    'pixiv': {
        'domains': ['pixiv.net', 'www.pixiv.net'],
        'replace': 'phixiv.net'
    }
}

NORMAL_PLATFORMS = ['twitter', 'tiktok', 'instagram', 'pixiv', 'anilist']
EXPERIMENTAL_PLATFORMS = ['facebook']

class EmbedConfigView(discord.ui.View):
    def __init__(self, guild_id, config):
        super().__init__(timeout=900) # 15 minutes timeout
        self.guild_id = guild_id
        self.config = config.copy()
        self.update_components()

    def update_components(self):
        self.clear_items()
        
        # Master Toggle Button
        master_enabled = self.config.get("master", True)
        style = discord.ButtonStyle.success if master_enabled else discord.ButtonStyle.danger
        label = "Master Toggle: ON" if master_enabled else "Master Toggle: OFF"
        btn = discord.ui.Button(label=label, style=style, custom_id="toggle_master", row=0)
        btn.callback = self.toggle_master
        self.add_item(btn)

        # Normal Platforms Select Menu
        normal_options = []
        for platform in NORMAL_PLATFORMS:
            enabled = self.config.get(platform, True)
            desc = "Currently Enabled" if enabled else "Currently Disabled"
            normal_options.append(discord.SelectOption(
                label=platform.capitalize(),
                description=f"Auto-fix {platform.capitalize()} links ({desc})",
                value=platform,
                default=enabled
            ))

        normal_select = discord.ui.Select(
            custom_id="normal_platform_select",
            placeholder="Select normal platforms to enable...",
            min_values=0,
            max_values=len(NORMAL_PLATFORMS),
            options=normal_options,
            disabled=not master_enabled,
            row=1
        )
        normal_select.callback = self.normal_select_callback
        self.add_item(normal_select)

        # Experimental Platforms Select Menu
        exp_options = []
        for platform in EXPERIMENTAL_PLATFORMS:
            enabled = self.config.get(platform, False)
            desc = "Currently Enabled" if enabled else "Currently Disabled"
            exp_options.append(discord.SelectOption(
                label=platform.capitalize(),
                description=f"Auto-fix {platform.capitalize()} links ({desc})",
                value=platform,
                default=enabled
            ))

        exp_select = discord.ui.Select(
            custom_id="exp_platform_select",
            placeholder="Select experimental platforms to enable...",
            min_values=0,
            max_values=len(EXPERIMENTAL_PLATFORMS),
            options=exp_options,
            disabled=not master_enabled,
            row=2
        )
        exp_select.callback = self.exp_select_callback
        self.add_item(exp_select)

    async def toggle_master(self, interaction: discord.Interaction):
        self.config["master"] = not self.config.get("master", True)
        await self.save_and_update(interaction)

    async def normal_select_callback(self, interaction: discord.Interaction):
        selected = interaction.data.get('values', [])
        for platform in NORMAL_PLATFORMS:
            self.config[platform] = platform in selected
        await self.save_and_update(interaction)

    async def exp_select_callback(self, interaction: discord.Interaction):
        selected = interaction.data.get('values', [])
        for platform in EXPERIMENTAL_PLATFORMS:
            self.config[platform] = platform in selected
        await self.save_and_update(interaction)

    async def save_and_update(self, interaction: discord.Interaction):
        # Save to DB
        await data_manager.set_server_config(self.guild_id, "embed_fixer", self.config)
        self.update_components()
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    def create_embed(self):
        embed = discord.Embed(title="🔗 Auto Link Fixer Configuration", color=discord.Color.blurple())
        embed.description = "Use the dropdown below to select which platforms should have their links automatically fixed."
        return embed

class LinkFixer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="embedconfig", description="Configure the Auto Link Fixer.")
    @app_commands.check(is_admin_or_role)
    async def embedconfig(self, interaction: discord.Interaction):
        server_config = await data_manager.get_server_config(interaction.guild_id)
        config = server_config.get("embed_fixer", {})
        
        view = EmbedConfigView(interaction.guild_id, config)
        embed = view.create_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        urls = re.findall(URL_REGEX, message.content)
        if not urls:
            return

        server_config = await data_manager.get_server_config(message.guild.id)
        config = server_config.get("embed_fixer", {})
        
        if not config.get("master", True):
            return

        fixed_links = []
        for url in urls:
            try:
                parsed = urlparse(url)
                netloc = parsed.netloc.lower()
                
                # Custom AniList handling
                if "anilist.co" in netloc:
                    if config.get("anilist", True):
                        match = re.search(r'anilist\.co/(anime|manga|character|staff|user)/([^/]+)', url)
                        if match:
                            category, item_id = match.groups()
                            self.bot.dispatch("anilist_link_detected", message, category, item_id)
                            # Still suppress embed
                            await asyncio.sleep(1)
                            try:
                                await message.edit(suppress=True)
                            except discord.Forbidden:
                                pass
                            continue
                
                # Check each platform
                for platform, data in PLATFORM_MAP.items():
                    if netloc in data['domains']:
                        default_enabled = platform not in EXPERIMENTAL_PLATFORMS
                        if config.get(platform, default_enabled):
                            # Ensure we don't mess up paths
                            # Reconstruct URL with new netloc
                            new_url = url.replace(parsed.netloc, data['replace'], 1)
                            # Format as a clean hyperlink
                            fixed_links.append(f"[{platform.capitalize()} Post]({new_url})")
                        break
            except Exception:
                pass

        if fixed_links:
            # We have fixed links to send
            # Only send unique ones in case user pasted the same link twice
            fixed_links = list(dict.fromkeys(fixed_links))
            reply_content = "\n".join(fixed_links)
            
            # Wait a short time for Discord to generate the original embed so we can suppress it
            await asyncio.sleep(1)
            
            try:
                await message.edit(suppress=True)
            except discord.Forbidden:
                pass # Bot might not have manage_messages permission
                
            await message.reply(reply_content, mention_author=False)

async def setup(bot):
    await bot.add_cog(LinkFixer(bot))
