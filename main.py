import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

class YuuriBot(commands.Bot):
    def __init__(self):
        # Request specific intents
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None # Removed default help command
        )

    async def setup_hook(self):
        # Load cogs
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py") and not filename.startswith("__"):
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")
                    print(f"Loaded extension: {filename}")
                except Exception as e:
                    print(f"Failed to load extension {filename}: {e}")
                    
        # Sync slash commands globally
        print("Syncing slash commands...")
        await self.tree.sync()
        print("Slash commands synced!")

    async def on_ready(self):
        print(f"Logged in as {self.user.name} ({self.user.id})")
        print("------")

if __name__ == "__main__":
    bot = YuuriBot()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("Error: DISCORD_TOKEN not found in environment variables.")
        exit(1)
    bot.run(token)
