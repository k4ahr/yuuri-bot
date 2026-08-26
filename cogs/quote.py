import discord
from discord import app_commands
from discord.ext import commands
import io
import textwrap
import re
from PIL import Image, ImageDraw, ImageFont
from pilmoji import Pilmoji

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

    def parse_markdown(self, text):
        pattern = re.compile(r'(```.*?```|`.*?`|\*\*\*.*?\*\*\*|\*\*.*?\*\*|\*.*?\*|__.*?__|~~.*?~~|\|\|.*?\|\|)', flags=re.DOTALL)
        parts = pattern.split(text)
        tokens = []
        for part in parts:
            if not part: continue
            style = 'normal'
            if part.startswith('```') and part.endswith('```') and len(part) >= 6:
                style = 'codeblock'
                part = part[3:-3].strip('\n')
            elif part.startswith('`') and part.endswith('`') and len(part) >= 2:
                style = 'codeinline'
                part = part[1:-1]
            elif part.startswith('***') and part.endswith('***') and len(part) >= 6:
                style = 'bold_italic'
                part = part[3:-3]
            elif part.startswith('**') and part.endswith('**') and len(part) >= 4:
                style = 'bold'
                part = part[2:-2]
            elif part.startswith('*') and part.endswith('*') and len(part) >= 2:
                style = 'italic'
                part = part[1:-1]
            elif part.startswith('__') and part.endswith('__') and len(part) >= 4:
                style = 'underline'
                part = part[2:-2]
            elif part.startswith('~~') and part.endswith('~~') and len(part) >= 4:
                style = 'strikethrough'
                part = part[2:-2]
            elif part.startswith('||') and part.endswith('||') and len(part) >= 4:
                style = 'spoiler'
                part = part[2:-2]
            tokens.append({'text': part, 'style': style})
        return tokens

    def wrap_tokens(self, tokens, pilmoji_instance, fonts, max_width):
        lines = []
        current_line = []
        current_x = 0
        
        for token in tokens:
            style = token['style']
            font = fonts.get(style, fonts['normal'])
            if style in ('codeblock', 'codeinline'):
                font = fonts.get('code', fonts['normal'])
                
            text = token['text']
            
            if style == 'codeblock':
                cb_lines = text.split('\n')
                for i, cb_line in enumerate(cb_lines):
                    if current_x > 0 and i > 0:
                        lines.append(current_line)
                        current_line = []
                        current_x = 0
                    
                    parts = re.split(r'( )', cb_line)
                    for part in parts:
                        if not part: continue
                        w, _ = pilmoji_instance.getsize(part, font=font)
                        if current_x + w > max_width and current_x > 0 and part != " ":
                            lines.append(current_line)
                            current_line = []
                            current_x = 0
                        if current_x == 0 and part == " ":
                            continue
                        current_line.append({'text': part, 'font': font, 'style': style})
                        current_x += w
                    
                    if i < len(cb_lines) - 1:
                        lines.append(current_line)
                        current_line = []
                        current_x = 0
                continue

            parts = re.split(r'( )', text)
            for part in parts:
                if not part: continue
                
                w, _ = pilmoji_instance.getsize(part, font=font)
                
                if current_x + w > max_width and current_x > 0 and part != " ":
                    lines.append(current_line)
                    current_line = []
                    current_x = 0
                    
                if current_x == 0 and part == " ":
                    continue
                    
                current_line.append({'text': part, 'font': font, 'style': style})
                current_x += w
                
        if current_line:
            lines.append(current_line)
            
        return lines

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
        
        try:
            fonts = {
                'normal': ImageFont.truetype("assets/fonts/arial.ttf", 65),
                'bold': ImageFont.truetype("assets/fonts/arialbd.ttf", 65),
                'italic': ImageFont.truetype("assets/fonts/ariali.ttf", 65),
                'bold_italic': ImageFont.truetype("assets/fonts/arialbi.ttf", 65),
                'code': ImageFont.truetype("assets/fonts/consola.ttf", 55)
            }
            font_small = ImageFont.truetype("assets/fonts/arial.ttf", 45)
            font_watermark = ImageFont.truetype("assets/fonts/arial.ttf", 30)
        except:
            default_font = ImageFont.load_default()
            fonts = {
                'normal': default_font,
                'bold': default_font,
                'italic': default_font,
                'bold_italic': default_font,
                'code': default_font
            }
            font_small = default_font
            font_watermark = default_font
            
        with Pilmoji(base) as pilmoji:
            text = f'"{text}"'
            tokens = self.parse_markdown(text)
            lines = self.wrap_tokens(tokens, pilmoji, fonts, max_width=1360)
            
            line_spacing = 20
            
            text_height = 0
            for line in lines:
                max_h = 0
                for segment in line:
                    _, h = pilmoji.getsize(segment['text'], font=segment['font'])
                    if h > max_h: max_h = h
                text_height += max_h + line_spacing
            
            if lines:
                text_height -= line_spacing
                
            user_text = f"— {username}"
            _, user_height = pilmoji.getsize(user_text, font=font_small)
            
            total_height = text_height + 60 + user_height
            start_y = (height - total_height) // 2
            
            draw_base = ImageDraw.Draw(base)
            current_y = start_y
            for line in lines:
                line_width = sum([pilmoji.getsize(segment['text'], font=segment['font'])[0] for segment in line])
                x = 1100 + (1360 - line_width) // 2
                max_h = 0
                for segment in line:
                    _, h = pilmoji.getsize(segment['text'], font=segment['font'])
                    if h > max_h: max_h = h
                
                for segment in line:
                    w, h = pilmoji.getsize(segment['text'], font=segment['font'])
                    style = segment['style']
                    
                    if style == 'spoiler':
                        draw_base.rectangle([x, current_y, x+w, current_y+max_h], fill=(40, 40, 40))
                        pilmoji.text((x, current_y), segment['text'], font=segment['font'], fill=(80, 80, 80))
                    elif style in ('codeinline', 'codeblock'):
                        draw_base.rectangle([x, current_y, x+w, current_y+max_h], fill=(43, 45, 49))
                        pilmoji.text((x, current_y), segment['text'], font=segment['font'], fill=(220, 220, 220))
                    else:
                        pilmoji.text((x, current_y), segment['text'], font=segment['font'], fill="white")
                        
                        if style == 'underline':
                            line_y = current_y + max_h - (max_h // 10)
                            draw_base.line([x, line_y, x+w, line_y], fill="white", width=4)
                        elif style == 'strikethrough':
                            line_y = current_y + (max_h // 2)
                            draw_base.line([x, line_y, x+w, line_y], fill="white", width=4)
                    
                    x += w
                current_y += max_h + line_spacing
                
            current_y += 60 - line_spacing
            w, _ = pilmoji.getsize(user_text, font=font_small)
            x = 1100 + (1360 - w) // 2
            pilmoji.text((x, current_y), user_text, font=font_small, fill="gray")
            
            watermark_text = "Yuuri Bot made by Kabonaro"
            w, h = pilmoji.getsize(watermark_text, font=font_watermark)
            pilmoji.text((width - w - 40, height - h - 30), watermark_text, font=font_watermark, fill=(128, 128, 128))
            
        buffer = io.BytesIO()
        base.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

    async def create_quote(self, message: discord.Message):
        avatar_bytes = await message.author.display_avatar.with_format("png").with_size(1024).read()
        return await self.bot.loop.run_in_executor(None, self.generate_quote_image, avatar_bytes, message.content, message.author.display_name)

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
