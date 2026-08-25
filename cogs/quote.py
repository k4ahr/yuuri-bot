import discord
from discord import app_commands
from discord.ext import commands
import io
import textwrap
from PIL import Image, ImageDraw, ImageFont

class Quote(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ctx_menu = app_commands.ContextMenu(
            name='Quote',
            callback=self.quote_context_menu,
        )
        self.bot.tree.add_command(self.ctx_menu)

    async def cog_unload(self):
        self.bot.tree.remove_command(self.ctx_menu.name, type=self.ctx_menu.type)

    def generate_quote_image(self, avatar_bytes, text, username):
        width, height = 2560, 1080
        base = Image.new("RGB", (width, height), "black")
        
        try:
            avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
            avatar = avatar.resize((height, height), Image.Resampling.LANCZOS)
        except Exception as e:
            print(f"Failed to load avatar: {e}")
            return None
            
        mask = Image.new("L", (height, height), 255)
        draw = ImageDraw.Draw(mask)
        fade_start = 400
        fade_end = 1080
        for x in range(fade_start, fade_end):
            alpha = int(255 - (x - fade_start) / (fade_end - fade_start) * 255)
            draw.line([(x, 0), (x, height)], fill=alpha)
            
        avatar.putalpha(mask)
        base.paste(avatar, (0, 0), avatar)
        
        draw = ImageDraw.Draw(base)
        try:
            font_large = ImageFont.truetype("assets/fonts/arial.ttf", 65)
            font_small = ImageFont.truetype("assets/fonts/arial.ttf", 45)
            font_watermark = ImageFont.truetype("assets/fonts/arial.ttf", 30)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
            font_watermark = ImageFont.load_default()
            
        # Wrapping text dynamically, wider now since we have 2560 width
        wrapper = textwrap.TextWrapper(width=50)
        wrapped_text = wrapper.wrap(f'"{text}"')
        
        line_spacing = 20
        
        def get_text_height(font, text):
            bbox = font.getbbox(text)
            return bbox[3] - bbox[1] if bbox else 0
            
        def get_text_width(font, text):
            bbox = font.getbbox(text)
            return bbox[2] - bbox[0] if bbox else 0

        text_height = sum([get_text_height(font_large, line) for line in wrapped_text]) + (len(wrapped_text) - 1) * line_spacing
        
        user_text = f"— {username}"
        user_height = get_text_height(font_small, user_text)
        
        total_height = text_height + 60 + user_height
        start_y = (height - total_height) // 2
        
        current_y = start_y
        for line in wrapped_text:
            w = get_text_width(font_large, line)
            h = get_text_height(font_large, line)
            # Center in the space from x=1100 to x=2460 (width 1360)
            x = 1100 + (1360 - w) // 2
            draw.text((x, current_y), line, font=font_large, fill="white")
            current_y += h + line_spacing
            
        current_y += 60 - line_spacing
        w = get_text_width(font_small, user_text)
        x = 1100 + (1360 - w) // 2
        draw.text((x, current_y), user_text, font=font_small, fill="gray")
        
        # Add watermark
        watermark_text = "Made by Yuuri Bot"
        w = get_text_width(font_watermark, watermark_text)
        h = get_text_height(font_watermark, watermark_text)
        draw.text((width - w - 40, height - h - 30), watermark_text, font=font_watermark, fill=(128, 128, 128))
        
        buffer = io.BytesIO()
        base.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

    async def create_quote(self, message: discord.Message):
        avatar_bytes = await message.author.display_avatar.with_format("png").with_size(1024).read()
        return await self.bot.loop.run_in_executor(None, self.generate_quote_image, avatar_bytes, message.clean_content, message.author.display_name)

    @commands.command(name="quote")
    async def quote_prefix(self, ctx, message_id: int = None):
        if not ctx.message.reference and not message_id:
            return await ctx.send("Please reply to a message or provide a message ID to quote!")
            
        target_message = None
        if ctx.message.reference:
            target_message = ctx.message.reference.resolved
            if type(target_message) is discord.DeletedReferencedMessage:
                return await ctx.send("That message was deleted!")
            if target_message is None:
                try:
                    target_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                except:
                    return await ctx.send("Failed to fetch the replied message.")
        elif message_id:
            try:
                target_message = await ctx.channel.fetch_message(message_id)
            except discord.NotFound:
                return await ctx.send("Message not found in this channel.")
            except discord.Forbidden:
                return await ctx.send("I don't have permission to read that message.")

        if not target_message.content:
            return await ctx.send("Cannot quote an empty message.")

        async with ctx.typing():
            buffer = await self.create_quote(target_message)
            if buffer:
                await ctx.send(file=discord.File(fp=buffer, filename="quote.png"))
            else:
                await ctx.send("Failed to generate quote image.")

    @app_commands.command(name="quotes", description="Quote a message by its ID.")
    async def quote_slash(self, interaction: discord.Interaction, message_id: str):
        try:
            target_message = await interaction.channel.fetch_message(int(message_id))
        except Exception:
            return await interaction.response.send_message("Could not find that message in this channel.", ephemeral=True)
            
        if not target_message.content:
            return await interaction.response.send_message("Cannot quote an empty message.", ephemeral=True)
            
        await interaction.response.defer()
        buffer = await self.create_quote(target_message)
        if buffer:
            await interaction.followup.send(file=discord.File(fp=buffer, filename="quote.png"))
        else:
            await interaction.followup.send("Failed to generate quote image.")

    async def quote_context_menu(self, interaction: discord.Interaction, message: discord.Message):
        if not message.content:
            return await interaction.response.send_message("Cannot quote an empty message.", ephemeral=True)
            
        await interaction.response.defer()
        buffer = await self.create_quote(message)
        if buffer:
            await interaction.followup.send(file=discord.File(fp=buffer, filename="quote.png"))
        else:
            await interaction.followup.send("Failed to generate quote image.")

async def setup(bot):
    await bot.add_cog(Quote(bot))
