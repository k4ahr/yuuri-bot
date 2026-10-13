import os
import aiohttp
import discord
from discord.ext import commands

class No(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_url = os.getenv("NO_AS_A_SERVICE")

    @commands.hybrid_command(name="no", description="Get a reason to say no.")
    async def no_command(self, ctx: commands.Context):
        await ctx.defer()
        if not self.api_url:
            await ctx.send("NO_AS_A_SERVICE URL is not configured in .env")
            return
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url, timeout=10) as resp:
                    if resp.status == 200:
                        try:
                            data = await resp.json()
                            if isinstance(data, dict) and "reason" in data:
                                content = str(data["reason"])
                            else:
                                content = await resp.text()
                        except Exception:
                            content = await resp.text()

                        if len(content) > 2000:
                            content = content[:1997] + "..."
                        await ctx.send(content)
                    else:
                        await ctx.send(f"Yeah I want to but the API saying {resp.status}")
        except Exception as e:
            await ctx.send(f"Yeah I want to but the API saying {e}")

async def setup(bot):
    await bot.add_cog(No(bot))
