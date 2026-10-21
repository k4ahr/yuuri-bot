import discord
from discord.ext import commands
import asyncio

bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())

@commands.hybrid_group(name="vanmau", description="Commands for API", fallback="random")
async def vanmau_group(ctx: commands.Context):
    print("Called vanmau_group (fallback)")

@vanmau_group.command(name="get", description="Get a specific id")
async def get_post(ctx: commands.Context, post_id: int):
    print(f"Called get: {post_id}")

bot.add_command(vanmau_group)

print("Commands registered:")
for cmd in bot.walk_commands():
    print(cmd.qualified_name)
