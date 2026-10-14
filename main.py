import os
import random
import logging
from pathlib import Path
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from core.web_server import start_web_server
from core.data_manager import data_manager

load_dotenv()

async def get_prefix(bot, message):
    if not message.guild:
        return commands.when_mentioned_or("y!", "Y!")(bot, message)
    prefix = await data_manager.get_prefix(message.guild.id)
    if prefix.lower() == "y!":
        return commands.when_mentioned_or("y!", "Y!")(bot, message)
    
    prefixes = [prefix]
    if prefix != prefix.lower():
        prefixes.append(prefix.lower())
    if prefix != prefix.upper():
        prefixes.append(prefix.upper())
    return commands.when_mentioned_or(*prefixes)(bot, message)

def load_quotes():
    try:
        with open("assets/quotes.txt", "r", encoding="utf-8") as f:
            quotes = [line.strip() for line in f if line.strip()]
            return quotes if quotes else ["No quotes available"]
    except FileNotFoundError:
        return ["No quotes available"]

class YuuriBot(commands.Bot):
    def __init__(self):
        # Request specific intents
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(
            command_prefix=get_prefix,
            intents=intents,
            case_insensitive=True,
            help_command=None # Removed default help command
        )
        self.quotes = load_quotes()

        @self.before_invoke
        async def before_any_command(ctx):
            if ctx.interaction is None:
                await ctx.typing()

    async def setup_hook(self):
        self.change_status.start()
        # Load cogs
        logger = logging.getLogger('discord')
        cogs_dir = Path("./cogs")
        for file in cogs_dir.glob("*.py"):
            if not file.name.startswith("__"):
                try:
                    await self.load_extension(f"cogs.{file.stem}")
                    logger.info(f"Loaded extension: {file.name}")
                except Exception as e:
                    logger.error(f"Failed to load extension {file.name}: {e}")
                    
        # Start OAuth Web Server
        try:
            await start_web_server(self)
        except Exception as e:
            logger.error(f"Failed to start web server: {e}")

    @tasks.loop(minutes=10)
    async def change_status(self):
        if self.quotes:
            quote = random.choice(self.quotes)
            await self.change_presence(activity=discord.Game(name=quote))

    @change_status.before_loop
    async def before_change_status(self):
        await self.wait_until_ready()

    async def on_ready(self):
        logger = logging.getLogger('discord')
        logger.info(f"Logged in as {self.user.name} ({self.user.id})")
        logger.info("------")

if __name__ == "__main__":
    discord.utils.setup_logging()
    logger = logging.getLogger('discord')
    
    bot = YuuriBot()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.error("DISCORD_TOKEN not found in environment variables.")
        exit(1)
    bot.run(token, log_handler=None)
