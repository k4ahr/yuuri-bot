import discord
from discord import app_commands
from discord.ext import commands
import os

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Replies with Pong and network statistics!")
    async def ping_command(self, interaction: discord.Interaction):
        # Calculate API latency (WebSocket ping)
        api_latency = round(self.bot.latency * 1000)
        
        # Calculate interaction response time
        response_time = round((discord.utils.utcnow() - interaction.created_at).total_seconds() * 1000)

        embed = discord.Embed(
            title="🏓 Pong!",
            color=discord.Color.green()
        )
        embed.add_field(name="API Latency", value=f"{api_latency}ms", inline=True)
        embed.add_field(name="Response Time", value=f"{response_time}ms", inline=True)

        image_path = os.path.join("assets", "images", "ping.gif")
        file = None
        if os.path.exists(image_path):
            file = discord.File(image_path, filename="ping.gif")
            # Using set_image or set_thumbnail for the gif. Let's use image.
            embed.set_image(url="attachment://ping.gif")

        if file:
            await interaction.response.send_message(embed=embed, file=file)
        else:
            await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Ping(bot))
