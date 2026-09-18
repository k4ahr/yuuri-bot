import discord
from discord import app_commands
from discord.ext import commands
import aiohttp

class VanMau(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.base_url = "https://api.ditmenavi.com/api"

    vanmau = app_commands.Group(name="vanmau", description="Commands for Ditmenavi (Văn Mẫu) API")

    def create_post_embed(self, post: dict) -> discord.Embed:
        title = post.get("title", "No Title")
        content = post.get("content", "")
        
        # Truncate content to 4000 characters to respect Discord embed limits
        if len(content) > 4000:
            content = content[:3997] + "..."
            
        embed = discord.Embed(
            title=title,
            description=content,
            color=discord.Color.blurple()
        )
        
        post_id = post.get("id", "?")
        category = post.get("category", "Unknown")
        embed.set_footer(text=f"ID: {post_id} | Category: {category}")
        
        submitted_by = post.get("submittedBy")
        if submitted_by:
            name = submitted_by.get("globalName") or submitted_by.get("global_name") or submitted_by.get("username", "Unknown")
            avatar_url = submitted_by.get("avatar")
            
            if avatar_url and not avatar_url.startswith("http"):
                discord_id = submitted_by.get("discordId")
                if discord_id:
                    avatar_url = f"https://cdn.discordapp.com/avatars/{discord_id}/{avatar_url}.png"
            
            if avatar_url:
                embed.set_author(name=f"Submitted by {name}", icon_url=avatar_url)
            else:
                embed.set_author(name=f"Submitted by {name}")
                
        return embed

    @vanmau.command(name="random", description="Get a random văn mẫu")
    async def random_post(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/posts/random", timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        embed = self.create_post_embed(data)
                        await interaction.followup.send(embed=embed)
                    else:
                        await interaction.followup.send(f"Error fetching data from API (Status: {resp.status}).")
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")

    @vanmau.command(name="get", description="Get a specific văn mẫu by ID")
    @app_commands.describe(post_id="The numeric ID of the post")
    async def get_post(self, interaction: discord.Interaction, post_id: int):
        await interaction.response.defer()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/posts/{post_id}", timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        embed = self.create_post_embed(data)
                        await interaction.followup.send(embed=embed)
                    elif resp.status == 404:
                        await interaction.followup.send("Post not found.")
                    else:
                        await interaction.followup.send(f"Error fetching data from API (Status: {resp.status}).")
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")

    @vanmau.command(name="search", description="Search for văn mẫu")
    @app_commands.describe(query="The search term")
    async def search_posts(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/search", params={"q": query, "limit": 10}, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        posts = data.get("posts", [])
                        
                        if not posts:
                            await interaction.followup.send("No results found.")
                            return
                            
                        if len(posts) == 1:
                            embed = self.create_post_embed(posts[0])
                            await interaction.followup.send(embed=embed)
                            return
                            
                        embed = discord.Embed(
                            title=f"Search Results for '{query}'",
                            color=discord.Color.blurple()
                        )
                        
                        description_lines = []
                        for idx, post in enumerate(posts[:10], start=1):
                            title = post.get("title", "No Title")
                            post_id = post.get("id")
                            if len(title) > 80:
                                title = title[:77] + "..."
                            description_lines.append(f"**{idx}.** {title} `(ID: {post_id})`")
                            
                        embed.description = "\n".join(description_lines)
                        
                        total = data.get("total", 0)
                        footer_text = f"Showing top {len(posts)} results. Use /vanmau get <id> to view."
                        if total > len(posts):
                            footer_text += f" (Total: {total})"
                        embed.set_footer(text=footer_text)
                        
                        await interaction.followup.send(embed=embed)
                    else:
                        await interaction.followup.send(f"Error searching API (Status: {resp.status}).")
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")

    @vanmau.command(name="categories", description="List all available categories")
    async def list_categories(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/categories", timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        categories = data.get("categories", [])
                        
                        if not categories:
                            await interaction.followup.send("No categories found.")
                            return
                            
                        embed = discord.Embed(
                            title="Văn Mẫu Categories",
                            color=discord.Color.blurple()
                        )
                        
                        category_lines = []
                        for cat in categories:
                            name = cat.get("displayName", "Unknown")
                            slug = cat.get("category", "")
                            category_lines.append(f"• **{name}** (`{slug}`)")
                            
                        embed.description = "\n".join(category_lines)
                        await interaction.followup.send(embed=embed)
                    else:
                        await interaction.followup.send(f"Error fetching categories (Status: {resp.status}).")
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")

async def setup(bot):
    await bot.add_cog(VanMau(bot))
