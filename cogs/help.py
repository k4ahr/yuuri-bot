import discord
from discord import app_commands
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Shows a list of available commands and their descriptions.")
    async def help_command(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Yuuri Bot Help",
            description="Here is a list of all available commands you can use. Note that admin commands may be hidden or blocked if you don't have permissions.",
            color=discord.Color.blurple()
        )
        
        commands_list = self.bot.tree.get_commands()
        
        for cmd in commands_list:
            desc = cmd.description or "No description provided."
            embed.add_field(name=f"/{cmd.name}", value=desc, inline=False)
            
        embed.set_footer(text="Use / to open the native Discord command menu!")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Help(bot))
