import discord
from discord import app_commands
from discord.ext import commands
import aiohttp

class VanMau(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.base_url = "https://api.ditmenavi.com/api"

    @commands.hybrid_group(name="vanmau", description="Commands for Ditmenavi (Văn Mẫu) API", invoke_without_command=True)
    async def vanmau_group(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await self._fetch_random(ctx)

    def extract_content(self, post: dict) -> str:
        content = post.get("content", "No content found.")
        # Discord message limit is 2000 characters
        if len(content) > 2000:
            content = content[:1997] + "..."
        return content

    async def _fetch_random(self, ctx: commands.Context):
        await ctx.defer()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/posts/random", timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        content = self.extract_content(data)
                        await ctx.send(content)
                    else:
                        await ctx.send(f"Error fetching data from API (Status: {resp.status}).")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @vanmau_group.command(name="random", description="Get a random văn mẫu")
    async def random_post(self, ctx: commands.Context):
        await self._fetch_random(ctx)

    @vanmau_group.command(name="get", description="Get a specific văn mẫu by ID")
    @app_commands.describe(post_id="The numeric ID of the post")
    async def get_post(self, ctx: commands.Context, post_id: int):
        await ctx.defer()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/posts/{post_id}", timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        content = self.extract_content(data)
                        await ctx.send(content)
                    elif resp.status == 404:
                        await ctx.send("Post not found.")
                    else:
                        await ctx.send(f"Error fetching data from API (Status: {resp.status}).")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @vanmau_group.command(name="search", description="Search for văn mẫu")
    @app_commands.describe(query="The search term")
    async def search_posts(self, ctx: commands.Context, query: str):
        await ctx.defer()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/search", params={"q": query, "limit": 10}, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        posts = data.get("posts", [])
                        
                        if not posts:
                            await ctx.send("No results found.")
                            return
                            
                        if len(posts) == 1:
                            content = self.extract_content(posts[0])
                            await ctx.send(content)
                            return
                            
                        lines = [f"**Search Results for '{query}'**"]
                        
                        for idx, post in enumerate(posts[:10], start=1):
                            title = post.get("title", "No Title")
                            post_id = post.get("id")
                            if len(title) > 80:
                                title = title[:77] + "..."
                            lines.append(f"**{idx}.** {title} `(ID: {post_id})`")
                            
                        total = data.get("total", 0)
                        footer = f"\n*Showing top {len(posts)} results. Use /vanmau get <id> to view.*"
                        if total > len(posts):
                            footer = f"\n*Showing top {len(posts)} results out of {total}. Use /vanmau get <id> to view.*"
                        lines.append(footer)
                        
                        await ctx.send("\n".join(lines))
                    else:
                        await ctx.send(f"Error searching API (Status: {resp.status}).")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @vanmau_group.command(name="categories", description="List all available categories")
    async def list_categories(self, ctx: commands.Context):
        await ctx.defer()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/categories", timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        categories = data.get("categories", [])
                        
                        if not categories:
                            await ctx.send("No categories found.")
                            return
                            
                        lines = ["**Văn Mẫu Categories**"]
                        for cat in categories:
                            name = cat.get("displayName", "Unknown")
                            slug = cat.get("category", "")
                            lines.append(f"• **{name}** (`{slug}`)")
                            
                        await ctx.send("\n".join(lines))
                    else:
                        await ctx.send(f"Error fetching categories (Status: {resp.status}).")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

async def setup(bot):
    await bot.add_cog(VanMau(bot))
