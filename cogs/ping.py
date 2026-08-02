import discord
from discord import app_commands
from discord.ext import commands
import os
import time
import aiohttp

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Replies with Pong and network statistics!")
    async def ping_command(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        # Calculate API latency (WebSocket ping)
        api_latency = round(self.bot.latency * 1000)
        
        # Calculate interaction response time
        response_time = round((discord.utils.utcnow() - interaction.created_at).total_seconds() * 1000)

        # AniList API ping
        al_start = time.perf_counter()
        al_status = "Online 🟢"
        al_latency = 0
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post("https://graphql.anilist.co", json={"query": "{ SiteStatistics { users { pageInfo { total } } } }"}, timeout=5) as resp:
                    al_latency = round((time.perf_counter() - al_start) * 1000)
                    if resp.status != 200:
                        al_status = f"Down 🔴 ({resp.status})"
        except Exception:
            al_latency = round((time.perf_counter() - al_start) * 1000)
            al_status = "Down 🔴 (Timeout)"

        embed = discord.Embed(
            title="🏓 Pong!",
            color=discord.Color.green()
        )
        embed.add_field(name="Discord WS", value=f"{api_latency}ms", inline=True)
        embed.add_field(name="Interaction", value=f"{response_time}ms", inline=True)
        embed.add_field(name="AniList API", value=f"{al_status}\nLatency: {al_latency}ms", inline=False)

        image_path = os.path.join("assets", "images", "ping.gif")
        file = None
        if os.path.exists(image_path):
            file = discord.File(image_path, filename="ping.gif")
            # Using set_image or set_thumbnail for the gif. Let's use image.
            embed.set_image(url="attachment://ping.gif")

        if file:
            await interaction.followup.send(embed=embed, file=file)
        else:
            await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Ping(bot))
