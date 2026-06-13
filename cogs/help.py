import discord
from discord import app_commands
from discord.ext import commands
import os

CATEGORIES = {
    "Admin": ["setadminrole", "setsupporterrole", "setlogchannel", "addresponse", "listresponses", "removeresponse", "sethoneypot", "sethoneypotdm", "setnoichu", "ncreset"],
    "Supporter": ["say"],
    "Normal": ["nclb", "ncrank", "nccount", "ncdefine", "safebooru", "gas", "help"]
}

class HelpView(discord.ui.View):
    def __init__(self, bot, author_id):
        super().__init__(timeout=180)
        self.bot = bot
        self.author_id = author_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This help menu is not for you!", ephemeral=True)
            return False
        return True

    def generate_embed(self, category: str):
        embed = discord.Embed(
            title=f"Yuuri Bot Help - {category} Commands",
            description="Here are the commands available in this category.",
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

    @discord.ui.button(label="Normal", style=discord.ButtonStyle.primary, custom_id="help_normal")
    async def normal_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = self.generate_embed("Normal")
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="Supporter", style=discord.ButtonStyle.success, custom_id="help_supporter")
    async def supporter_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = self.generate_embed("Supporter")
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="Admin", style=discord.ButtonStyle.danger, custom_id="help_admin")
    async def admin_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = self.generate_embed("Admin")
        await interaction.response.edit_message(embed=embed)

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Shows a list of available commands categorized with buttons.")
    async def help_command(self, interaction: discord.Interaction):
        view = HelpView(self.bot, interaction.user.id)
        embed = view.generate_embed("Normal")
        
        image_path = os.path.join("assets", "images", "help_banner.png")
        file = None
        if os.path.exists(image_path):
            file = discord.File(image_path, filename="help_banner.png")
            
        if file:
            await interaction.response.send_message(embed=embed, view=view, file=file)
        else:
            await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Help(bot))
