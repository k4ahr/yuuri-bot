import discord
from discord import app_commands
from discord.ext import commands
from core.data_manager import data_manager
from cogs.admin import is_admin_or_role
import re

class Trigger(commands.GroupCog, group_name="trigger"):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @app_commands.command(name="add", description="Add a new auto-reply trigger for the server.")
    @app_commands.describe(word="The word or phrase to trigger on.", response="The response to send.")
    @app_commands.check(is_admin_or_role)
    async def trigger_add(self, interaction: discord.Interaction, word: str, response: str):
        config = await data_manager.get_server_config(interaction.guild_id)
        triggers = config.get("triggers", {})
        
        # Store in lowercase for case-insensitive matching
        word_lower = word.lower()
        triggers[word_lower] = response
        
        await data_manager.set_server_config(interaction.guild_id, "triggers", triggers)
        await interaction.response.send_message(f"Added trigger for `{word}` => `{response}`", ephemeral=True)

    @app_commands.command(name="remove", description="Remove an auto-reply trigger.")
    @app_commands.describe(word="The trigger word to remove.")
    @app_commands.check(is_admin_or_role)
    async def trigger_remove(self, interaction: discord.Interaction, word: str):
        config = await data_manager.get_server_config(interaction.guild_id)
        triggers = config.get("triggers", {})
        
        word_lower = word.lower()
        if word_lower in triggers:
            del triggers[word_lower]
            await data_manager.set_server_config(interaction.guild_id, "triggers", triggers)
            await interaction.response.send_message(f"Removed trigger for `{word}`.", ephemeral=True)
        else:
            await interaction.response.send_message(f"No trigger found for `{word}`.", ephemeral=True)

    @app_commands.command(name="list", description="List all auto-reply triggers.")
    @app_commands.check(is_admin_or_role)
    async def trigger_list(self, interaction: discord.Interaction):
        config = await data_manager.get_server_config(interaction.guild_id)
        triggers = config.get("triggers", {})
        
        if not triggers:
            return await interaction.response.send_message("No triggers configured for this server.", ephemeral=True)
            
        embed = discord.Embed(title="Auto-reply Triggers", color=discord.Color.blurple())
        
        text = "\n".join([f"**{word}** => {resp}" for word, resp in triggers.items()])
        if len(text) > 4096:
            text = text[:4090] + "..."
            
        embed.description = text
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        config = await data_manager.get_server_config(message.guild.id)
        triggers = config.get("triggers", {})
        if not triggers:
            return

        content_lower = message.content.lower()
        for word, response in triggers.items():
            escaped_word = re.escape(word)
            # Use bounded match so we don't trigger on substrings inside other words
            pattern = r'\b' + escaped_word + r'\b'
            if re.search(pattern, content_lower):
                await message.channel.send(response)
                break

async def setup(bot):
    await bot.add_cog(Trigger(bot))
