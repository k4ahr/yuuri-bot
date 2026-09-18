import asyncio
import discord
from discord.ext import commands

async def main():
    bot = commands.Bot(command_prefix='y!', intents=discord.Intents.default())
    try:
        await bot.load_extension('cogs.vanmau')
        print("Load successful!")
    except Exception as e:
        print(f"Error loading cog: {e}")

if __name__ == '__main__':
    asyncio.run(main())
