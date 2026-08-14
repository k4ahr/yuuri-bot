import discord
from discord import app_commands
from discord.ext import commands
import os

CATEGORIES = {
    "Wordchain": ["setnoichu", "ncreset", "nclb", "ncrank", "nccount", "ncdefine"],
    "AniList": ["anilist"],
    "General": ["safebooru", "gas", "help", "ping", "privacy", "whatsnew"],
    "Supporter": ["say", "addresponse", "listresponses", "removeresponse", "danbooru"],
    "Admin": ["rolesconfig", "setlogchannel", "sethoneypot", "sethoneypotdm", "embedconfig", "botstats", "trigger"]
}

class HelpSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="General", description="General & utility commands", emoji="📁"),
            discord.SelectOption(label="Wordchain", description="Wordchain game commands", emoji="🔤"),
            discord.SelectOption(label="AniList", description="Anime & Manga search", emoji="🎌"),
            discord.SelectOption(label="Supporter", description="Commands for bot supporters", emoji="🌟"),
            discord.SelectOption(label="Admin", description="Server configuration & moderation", emoji="🛡️")
        ]
        super().__init__(placeholder="Choose a command category...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        embed = self.view.generate_embed(self.values[0])
        await interaction.response.edit_message(embed=embed)

class HelpView(discord.ui.View):
    def __init__(self, bot, author_id):
        super().__init__(timeout=180)
        self.bot = bot
        self.author_id = author_id
        self.add_item(HelpSelect())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This help menu is not for you!", ephemeral=True)
            return False
        return True

    def generate_embed(self, category: str):
        emojis = {"General": "📁", "Wordchain": "🔤", "AniList": "🎌", "Supporter": "🌟", "Admin": "🛡️"}
        emoji = emojis.get(category, "📁")
        
        embed = discord.Embed(
            title=f"{emoji} Yuuri Bot Help - {category} Commands",
            description="Here are the commands available in this category.\n\n💡 *Try to run `/whatsnew` to see the newest command and features!*",
            color=discord.Color.blurple()
        )
        
        all_commands = {cmd.name: cmd for cmd in self.bot.tree.get_commands()}
        cat_commands = CATEGORIES.get(category, [])
        
        count = 0
        for name in cat_commands:
            cmd = all_commands.get(name)
            if cmd:
                desc = cmd.description or "No description provided."
                embed.add_field(name=f"/{cmd.name}", value=desc, inline=False)
                count += 1
                
        if count == 0:
            embed.add_field(name="No commands loaded", value="Commands are either not synced or unavailable right now.", inline=False)
                
        embed.set_footer(text="Use / to open the native Discord command menu!")
        
        image_path = os.path.join("assets", "images", "help_banner.png")
        if os.path.exists(image_path):
            embed.set_image(url="attachment://help_banner.png")
            
        return embed

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Shows a list of available commands categorized with a dropdown.")
    async def help_command(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        view = HelpView(self.bot, interaction.user.id)
        embed = view.generate_embed("General")
        
        image_path = os.path.join("assets", "images", "help_banner.png")
        file = None
        if os.path.exists(image_path):
            file = discord.File(image_path, filename="help_banner.png")
            
        if file:
            await interaction.followup.send(embed=embed, view=view, file=file)
        else:
            await interaction.followup.send(embed=embed, view=view)

    @app_commands.command(name="privacy", description="See the bot's privacy terms")
    async def privacy_command(self, interaction: discord.Interaction):
        image_path = os.path.join("assets", "images", "privacy.jpg")
        if os.path.exists(image_path):
            file = discord.File(image_path, filename="privacy.jpg")
            await interaction.response.send_message(file=file)
        else:
            await interaction.response.send_message("The privacy terms image is currently unavailable.")

    @app_commands.command(name="whatsnew", description="See the newest features and functions.")
    async def whatsnew_command(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="✨ What's New in Yuuri Bot?",
            description="Here are the latest features and updates!\n\n• **Texting Triggers**: Now you can add a trigger respond depending on what people send using `/trigger add | list | remove` to manage and adding trigger!\n • **AniList Integration**: We now have AniList integration! Check out at `/anilist` to get a list of commands!",
            color=discord.Color.gold()
        )
        
        image_path = os.path.join("assets", "images", "new.gif")
        file = None
        if os.path.exists(image_path):
            file = discord.File(image_path, filename="new.gif")
            embed.set_image(url="attachment://new.gif")
            
        if file:
            await interaction.response.send_message(embed=embed, file=file)
        else:
            await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))
