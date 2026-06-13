import discord
from discord.ext import commands
import random
from core.data_manager import data_manager

class AutoReply(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # Check if the bot is mentioned
        if self.bot.user in message.mentions:
            config = await data_manager.get_server_config(message.guild.id)
            responses = config.get("mention_responses", [])
            if responses:
                reply = random.choice(responses)
                await message.reply(reply)

async def setup(bot):
    await bot.add_cog(AutoReply(bot))
