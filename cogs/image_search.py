import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import random

class ImageSearch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="safebooru", description="Searches safebooru.org for images based on tags.")
    @app_commands.describe(tags="Tags to search for (space-separated).")
    async def safebooru_search(self, interaction: discord.Interaction, tags: str = ""):
        await interaction.response.defer()
        
        formatted_tags = tags.replace(" ", "+")
        url = f"https://safebooru.org/index.php?page=dapi&s=post&q=index&json=1&tags={formatted_tags}&limit=100"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        await interaction.followup.send("Failed to fetch images from safebooru.")
                        return
                    
                    try:
                        data = await resp.json(content_type=None)
                    except:
                        await interaction.followup.send("Invalid response from Safebooru.")
                        return
                    
                    if not data:
                        await interaction.followup.send(f"No images found for tags: `{tags}`")
                        return
                        
                    image = random.choice(data)
                    image_url = f"https://safebooru.org/images/{image['directory']}/{image['image']}"
                    post_url = f"https://safebooru.org/index.php?page=post&s=view&id={image['id']}"
                    
                    embed = discord.Embed(title=f"Safebooru Search: {tags}" if tags else "Safebooru Random Search", url=post_url, color=discord.Color.blue())
                    embed.set_image(url=image_url)
                    
                    img_tags = image.get("tags", "")
                    if len(img_tags) > 80:
                        img_tags = img_tags[:77] + "..."
                        
                    embed.set_footer(text=f"Score: {image.get('score', 0)} | Tags: {img_tags}")
                    
                    await interaction.followup.send(embed=embed)
            except Exception as e:
                await interaction.followup.send(f"An error occurred while fetching image: {e}")

    @app_commands.command(name="danbooru", description="Searches danbooru.donmai.us for images (Supporter only, NSFW channels only).")
    @app_commands.describe(tags="Tags to search for (space-separated, max 2 tags).")
    async def danbooru_search(self, interaction: discord.Interaction, tags: str = ""):
        # Check NSFW channel
        if not getattr(interaction.channel, 'is_nsfw', lambda: False)():
            return await interaction.response.send_message("❌ This command can only be used in **NSFW** channels.", ephemeral=True)
            
        # Check supporter or admin
        from cogs.admin import is_supporter_or_admin
        if not await is_supporter_or_admin(interaction):
            return
            
        await interaction.response.defer()
        
        # Danbooru allows maximum 2 tags for anonymous users
        tag_list = tags.split()
        if len(tag_list) > 2:
            return await interaction.followup.send("❌ Danbooru only allows searching up to 2 tags at a time.")
            
        formatted_tags = "+".join(tag_list)
        url = f"https://danbooru.donmai.us/posts.json?tags={formatted_tags}&limit=100"
        
        async with aiohttp.ClientSession() as session:
            try:
                headers = {"User-Agent": "YuuriBot/1.0 (by discord user)"}
                async with session.get(url, headers=headers) as resp:
                    if resp.status != 200:
                        return await interaction.followup.send("❌ Failed to fetch images from Danbooru.")
                    
                    try:
                        data = await resp.json(content_type=None)
                    except:
                        return await interaction.followup.send("❌ Invalid response from Danbooru.")
                    
                    valid_images = [img for img in data if 'file_url' in img]
                    
                    if not valid_images:
                        return await interaction.followup.send(f"❌ No images found for tags: `{tags}`")
                        
                    image = random.choice(valid_images)
                    image_url = image['file_url']
                    post_url = f"https://danbooru.donmai.us/posts/{image['id']}"
                    
                    embed = discord.Embed(title=f"Danbooru Search: {tags}" if tags else "Danbooru Random Search", url=post_url, color=discord.Color.red())
                    embed.set_image(url=image_url)
                    
                    img_tags = image.get("tag_string", "")
                    if len(img_tags) > 80:
                        img_tags = img_tags[:77] + "..."
                        
                    embed.set_footer(text=f"Score: {image.get('score', 0)} | Tags: {img_tags}")
                    
                    await interaction.followup.send(embed=embed)
            except Exception as e:
                await interaction.followup.send(f"❌ An error occurred while fetching image: {e}")

async def setup(bot):
    await bot.add_cog(ImageSearch(bot))
