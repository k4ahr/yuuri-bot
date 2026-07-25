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
        'replace': 'vxtwitter.com'
    },
    'tiktok': {
        'domains': ['tiktok.com', 'www.tiktok.com', 'vm.tiktok.com'],
        'replace': 'vxtiktok.com'
    },
    'instagram': {
        'domains': ['instagram.com', 'www.instagram.com'],
        'replace': 'ddinstagram.com'
    },
    'reddit': {
        'domains': ['reddit.com', 'www.reddit.com', 'old.reddit.com'],
        'replace': 'rxddit.com'
    },
    'facebook': {
        'domains': ['facebook.com', 'www.facebook.com', 'fb.watch', 'www.fb.watch'],
        'replace': 'facebed.com'
    }
}

class EmbedConfigView(discord.ui.View):
    def __init__(self, guild_id, config):
        super().__init__(timeout=900) # 15 minutes timeout
        self.guild_id = guild_id
        self.config = config.copy()
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        
        # Master Toggle
        master_enabled = self.config.get("master", True)
        style = discord.ButtonStyle.success if master_enabled else discord.ButtonStyle.danger
        label = "Master: ON" if master_enabled else "Master: OFF"
        btn = discord.ui.Button(label=label, style=style, custom_id="toggle_master", row=0)
        btn.callback = self.toggle_master
        self.add_item(btn)

        # Platform toggles
        platforms = ['twitter', 'tiktok', 'instagram', 'reddit', 'facebook']
        for i, platform in enumerate(platforms):
            enabled = self.config.get(platform, True)
            p_style = discord.ButtonStyle.success if enabled else discord.ButtonStyle.danger
            p_label = f"{platform.capitalize()}: ON" if enabled else f"{platform.capitalize()}: OFF"
            # Disable platform buttons if master is OFF
            p_btn = discord.ui.Button(label=p_label, style=p_style, custom_id=f"toggle_{platform}", row=1 + (i//3), disabled=not master_enabled)
            p_btn.callback = self.create_callback(platform)
            self.add_item(p_btn)

    async def toggle_master(self, interaction: discord.Interaction):
        self.config["master"] = not self.config.get("master", True)
        await self.save_and_update(interaction)

    def create_callback(self, platform):
        async def callback(interaction: discord.Interaction):
            self.config[platform] = not self.config.get(platform, True)
            await self.save_and_update(interaction)
        return callback

    async def save_and_update(self, interaction: discord.Interaction):
        # Save to DB
        await data_manager.set_server_config(self.guild_id, "embed_fixer", self.config)
        self.update_buttons()
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    def create_embed(self):
        embed = discord.Embed(title="🔗 Auto Link Fixer Configuration", color=discord.Color.blurple())
        embed.description = "Toggle which platforms should have their links automatically fixed."
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
                
                # Check each platform
                for platform, data in PLATFORM_MAP.items():
                    if netloc in data['domains']:
                        if config.get(platform, True):
                            # Ensure we don't mess up paths
                            # Reconstruct URL with new netloc
                            new_url = url.replace(parsed.netloc, data['replace'], 1)
                            # Prefix with a zero-width space if needed to avoid discord parsing issues? No, standard is fine
                            fixed_links.append(new_url)
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
