import discord
from discord.ext import commands
import io
import os
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageSequence
import asyncio

class InitialFormatSelectView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=120.0)
        self.ctx = ctx
        self.format_chosen = None

    @discord.ui.button(label="Webp", style=discord.ButtonStyle.primary)
    async def btn_webp(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("This is not for you.", ephemeral=True)
        self.format_chosen = 'webp'
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="Gif", style=discord.ButtonStyle.primary)
    async def btn_gif(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("This is not for you.", ephemeral=True)
        self.format_chosen = 'gif'
        await interaction.response.defer()
        self.stop()

class FormatSelectViewInternal(discord.ui.View):
    def __init__(self, parent_view):
        super().__init__(timeout=60.0)
        self.parent_view = parent_view
        self.format_chosen = None
        
    @discord.ui.button(label="Webp", style=discord.ButtonStyle.primary)
    async def btn_webp(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.parent_view.ctx.author:
            return await interaction.response.send_message("This is not for you.", ephemeral=True)
        self.format_chosen = 'webp'
        await interaction.response.defer()
        await interaction.delete_original_response()
        self.stop()
        
    @discord.ui.button(label="Gif", style=discord.ButtonStyle.primary)
    async def btn_gif(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.parent_view.ctx.author:
            return await interaction.response.send_message("This is not for you.", ephemeral=True)
        self.format_chosen = 'gif'
        await interaction.response.defer()
        await interaction.delete_original_response()
        self.stop()

class BubbleSelectViewInternal(discord.ui.View):
    def __init__(self, parent_view):
        super().__init__(timeout=60.0)
        self.parent_view = parent_view
        self.bubble_chosen = None
        
    @discord.ui.button(label="Right", style=discord.ButtonStyle.primary)
    async def btn_right(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.parent_view.ctx.author:
            return await interaction.response.send_message("This is not for you.", ephemeral=True)
        self.bubble_chosen = 'right'
        await interaction.response.defer()
        await interaction.delete_original_response()
        self.stop()
        
    @discord.ui.button(label="Left", style=discord.ButtonStyle.primary)
    async def btn_left(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.parent_view.ctx.author:
            return await interaction.response.send_message("This is not for you.", ephemeral=True)
        self.bubble_chosen = 'left'
        await interaction.response.defer()
        await interaction.delete_original_response()
        self.stop()

class GifMakerView(discord.ui.View):
    def __init__(self, ctx, initial_bytes, initial_format='webp', is_video=False):
        super().__init__(timeout=600)
        self.ctx = ctx
        self.history = [initial_bytes]
        self.current_format = initial_format
        self.is_video = is_video
        
    async def update_message(self, interaction):
        if not self.history:
            return
        current_bytes = self.history[-1]
        file = discord.File(io.BytesIO(current_bytes), filename=f"output.{self.current_format}")
        await interaction.message.edit(attachments=[file], view=self)

    @discord.ui.select(
        placeholder="Choose an action...",
        options=[
            discord.SelectOption(label="Speed up/slow down", value="speed", description="Change gif speed"),
            discord.SelectOption(label="Reduce resolution", value="resize", description="Reduce resolution by %"),
            discord.SelectOption(label="Add speech bubble", value="bubble", description="Add a bubble speech on top"),
            discord.SelectOption(label="Optimize gif", value="optimize", description="Optimize the gif"),
            discord.SelectOption(label="Convert to", value="convert_format", description="Change output format"),
            discord.SelectOption(label="Add whitebox caption", value="caption", description="Add a whitebox caption on top"),
            discord.SelectOption(label="Undo", value="undo", description="Revert last change")
        ]
    )
    async def select_action(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("This is not your command.", ephemeral=True)
            
        action = select.values[0]
        select.placeholder = "Choose an action..."
        
        if action == "undo":
            if len(self.history) > 1:
                self.history.pop()
                await interaction.response.defer()
                await self.update_message(interaction)
            else:
                await interaction.response.send_message("Nothing to undo.", ephemeral=True)
            return

        # Get current image
        current_bytes = self.history[-1]
        
        if action == "speed":
            modal = SpeedModal(self)
            await interaction.response.send_modal(modal)
            return
            
        elif action == "resize":
            modal = ResizeModal(self)
            await interaction.response.send_modal(modal)
            return
            
        elif action == "bubble":
            embed = discord.Embed(description="Choose the bubble direction:")
            view = BubbleSelectViewInternal(self)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            await view.wait()
            if view.bubble_chosen:
                msg = await interaction.message.channel.send("Adding bubble...", delete_after=3)
                await self.process_image_action("bubble", direction=view.bubble_chosen)
                await interaction.message.edit(
                    attachments=[discord.File(io.BytesIO(self.history[-1]), filename=f"output.{self.current_format}")], 
                    view=self
                )
            return
            
        elif action == "convert_format":
            embed = discord.Embed(
                description="Choose the format you want to convert\n"
                            "**Webp**: Better optimization, better quality, better for transparency image from PNG/APNG\n"
                            "**Gif**: Better legacy support, use this if you import a static image and Discord do detect this as an animated image"
            )
            view = FormatSelectViewInternal(self)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            await view.wait()
            if view.format_chosen:
                self.current_format = view.format_chosen
                msg = await interaction.message.channel.send("Converting format...", delete_after=3)
                await self.process_image_action("convert_format", format=view.format_chosen)
                await interaction.message.edit(
                    attachments=[discord.File(io.BytesIO(self.history[-1]), filename=f"output.{self.current_format}")], 
                    view=self
                )
            return
            
        elif action == "caption":
            await interaction.response.send_message("Please type the caption in your next message (you have 60 seconds):")
            
            def check(m):
                return m.author == self.ctx.author and m.channel == self.ctx.channel
                
            try:
                msg = await self.ctx.bot.wait_for('message', timeout=60.0, check=check)
                caption_text = msg.content[:100]
                if len(msg.content) > 100:
                    await interaction.message.channel.send("Caption was longer than 100 characters and has been truncated.", delete_after=5)
                await self.process_image_action("caption", caption_text=caption_text)
                await interaction.message.channel.send("Caption applied!", delete_after=3)
                await self.update_message(interaction)
            except asyncio.TimeoutError:
                await interaction.message.channel.send("You took too long to reply.", delete_after=5)
            return

        else:
            await interaction.response.defer()
            await self.process_image_action(action)
            await self.update_message(interaction)

    async def process_image_action(self, action, **kwargs):
        current_bytes = self.history[-1]
        
        def process_img():
            try:
                img = Image.open(io.BytesIO(current_bytes))
            except Exception as e:
                print(f"Error opening image: {e}")
                return None
                
            frames = []
            durations = []
            
            if action == "bubble":
                direction = kwargs.get("direction", "right")
                try:
                    bubble = Image.open(f"assets/images/bubble_{direction}.png").convert("RGBA")
                except Exception:
                    bubble = None
                    
            for frame in ImageSequence.Iterator(img):
                f = frame.copy()
                if f.mode != 'RGBA':
                    f = f.convert('RGBA')
                    
                dur = frame.info.get('duration', 100)
                if action == "speed":
                    mult = kwargs.get('multiplier', 1.0)
                    dur = int(dur / mult)
                durations.append(dur)
                
                if action == "resize":
                    pct = kwargs.get('percentage', 100) / 100.0
                    f = f.resize((int(f.width * pct), int(f.height * pct)), Image.Resampling.LANCZOS)
                
                elif action == "bubble" and bubble:
                    b = bubble.resize((f.width, int(bubble.height * (f.width / bubble.width))), Image.Resampling.LANCZOS)
                    f.paste(b, (0, 0), b)
                    
                elif action == "caption":
                    text = kwargs.get('caption_text', '')[:100]
                    target_width = f.width * 0.95
                    
                    # Scale font down based on length (1.0 at 0 chars to ~0.5 at 100 chars)
                    scale_factor = max(0.5, 1.0 - (len(text) / 200))
                    fontsize = int((f.width / 8) * scale_factor)
                    if fontsize < 12: fontsize = 12
                    
                    font_path = "assets/fonts/impact.ttf"
                    if not os.path.exists(font_path):
                        font_path = "assets/fonts/arialbd.ttf"
                        
                    try:
                        font = ImageFont.truetype(font_path, fontsize)
                    except:
                        font = ImageFont.load_default()
                    
                    # Very basic word wrap
                    avg_char_width = sum(font.getbbox(c)[2] for c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ') / 52
                    if avg_char_width == 0: avg_char_width = 10
                    wrap_width = max(1, int(target_width / avg_char_width))
                    lines = textwrap.wrap(text, width=wrap_width)
                    
                    # Ensure bbox works for calculating height
                    try:
                        line_height = font.getbbox("A")[3] + 10
                    except AttributeError:
                        line_height = fontsize + 10
                        
                    padding_top = 30
                    padding_bottom = 30
                    text_box_height = len(lines) * line_height + padding_top + padding_bottom
                    
                    new_f = Image.new('RGBA', (f.width, f.height + text_box_height), (0, 0, 0, 0))
                    
                    d = ImageDraw.Draw(new_f)
                    d.rectangle([0, 0, f.width, text_box_height], fill=(255, 255, 255, 255))
                    
                    new_f.paste(f, (0, text_box_height))
                    y_text = padding_top
                    for line in lines:
                        try:
                            line_width = font.getlength(line)
                        except AttributeError:
                            line_width = len(line) * avg_char_width
                        x_text = (f.width - line_width) / 2
                        
                        d.text((x_text, y_text), line, font=font, fill=(0,0,0,255))
                        y_text += line_height
                        
                    f = new_f
                    
                frames.append(f)
                
            out = io.BytesIO()
            save_kwargs = {
                'save_all': True,
                'append_images': frames[1:],
                'duration': durations,
                'loop': img.info.get('loop', 0)
            }
            
            if len(frames) == 1:
                frames.append(frames[0].copy())
                durations.append(100)
                save_kwargs['append_images'] = frames[1:]
                save_kwargs['duration'] = durations
                save_kwargs['save_all'] = True
                save_kwargs['loop'] = 0
            
            if action == "optimize":
                save_kwargs['optimize'] = True
                
            if action == "convert_format":
                self.current_format = kwargs.get('format', self.current_format).lower()
                
            format_to_save = 'GIF' if self.current_format == 'gif' else 'WEBP'
            self.current_format = format_to_save.lower()
            if format_to_save == 'WEBP':
                save_kwargs['method'] = 6
                if 'optimize' in save_kwargs:
                    del save_kwargs['optimize']
            else:
                save_kwargs['disposal'] = 2
                    
            frames[0].save(out, format=format_to_save, **save_kwargs)
            return out.getvalue()
            
        loop = asyncio.get_running_loop()
        new_bytes = await loop.run_in_executor(None, process_img)
        if new_bytes:
            self.history.append(new_bytes)

class SpeedModal(discord.ui.Modal, title='Change Speed'):
    multiplier = discord.ui.TextInput(
        label='Speed multiplier (e.g. 1.5, 0.5)',
        style=discord.TextStyle.short,
        default='1.5'
    )

    def __init__(self, view):
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        try:
            mult = float(self.multiplier.value)
            if mult <= 0:
                raise ValueError
        except ValueError:
            return await interaction.response.send_message("Invalid multiplier.", ephemeral=True)
            
        await interaction.response.defer()
        await self.view.process_image_action("speed", multiplier=mult)
        await self.view.update_message(interaction)

class ResizeModal(discord.ui.Modal, title='Reduce Resolution'):
    percentage = discord.ui.TextInput(
        label='Percentage (1-100)',
        style=discord.TextStyle.short,
        default='50'
    )

    def __init__(self, view):
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        try:
            pct = int(self.percentage.value)
            if pct <= 0 or pct > 100:
                raise ValueError
        except ValueError:
            return await interaction.response.send_message("Invalid percentage.", ephemeral=True)
            
        await interaction.response.defer()
        await self.view.process_image_action("resize", percentage=pct)
        await self.view.update_message(interaction)


class GifMakerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="gifmaker", aliases=["gm"])
    async def gifmaker(self, ctx):
        attachment = None
        if ctx.message.attachments:
            attachment = ctx.message.attachments[0]
        elif ctx.message.reference and ctx.message.reference.resolved:
            ref_msg = ctx.message.reference.resolved
            if ref_msg.attachments:
                attachment = ref_msg.attachments[0]
                
        img_bytes = None
        content_type = ""
        filename = ""

        if attachment:
            img_bytes = await attachment.read()
            content_type = (attachment.content_type or '').lower()
            filename = attachment.filename.lower()
        else:
            if ctx.message.reference and hasattr(ctx.message.reference.resolved, 'embeds'):
                ref_msg = ctx.message.reference.resolved
                if ref_msg.embeds:
                    embed = ref_msg.embeds[0]
                    url = None
                    if embed.video and embed.video.url:
                        url = embed.video.url
                    elif embed.image and embed.image.url:
                        url = embed.image.url
                    elif embed.thumbnail and embed.thumbnail.url:
                        url = embed.thumbnail.url
                    
                    if url:
                        import aiohttp
                        async with aiohttp.ClientSession() as session:
                            async with session.get(url) as resp:
                                if resp.status == 200:
                                    img_bytes = await resp.read()
                                    content_type = resp.headers.get('content-type', '').lower()
                                    filename = url.split('/')[-1].split('?')[0].lower()
            
        if not img_bytes:
            return await ctx.send("Please attach an image/video, reply to a message containing one, or reply to a link containing media.")
            
        is_video = False
        if content_type.startswith('video/') or filename.endswith(('.mp4', '.mov', '.webm', '.mkv', '.avi')):
            is_video = True
                
        if is_video:
            import tempfile
            import subprocess
            with tempfile.NamedTemporaryFile(delete=False) as temp_in:
                temp_in.write(img_bytes)
                in_path = temp_in.name
                
            out_path = in_path + ".webp"
            try:
                probe_proc = await asyncio.create_subprocess_exec(
                    'ffprobe', '-v', 'error', '-show_entries', 'format=duration', 
                    '-of', 'default=noprint_wrappers=1:nokey=1', in_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.DEVNULL
                )
                stdout, _ = await probe_proc.communicate()
                try:
                    duration = float(stdout.decode('utf-8').strip())
                    if duration > 20.5:
                        os.remove(in_path)
                        return await ctx.send(f"Media is too long! The length is {duration:.1f}s, but the maximum allowed length is 20 seconds.")
                except ValueError:
                    pass

                proc = await asyncio.create_subprocess_exec(
                    'ffmpeg', '-y', '-i', in_path, '-t', '20', '-vf', "scale='min(480,iw)':-2,fps=15",
                    '-c:v', 'libwebp', '-lossless', '0', '-q:v', '85', '-compression_level', '4', '-preset', 'default', '-loop', '0', '-an', out_path,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL
                )
                await proc.communicate()
                if os.path.exists(out_path):
                    with open(out_path, 'rb') as f:
                        img_bytes = f.read()
                    os.remove(out_path)
                else:
                    return await ctx.send("Failed to process media. FFmpeg might not be installed or failed.")
            except FileNotFoundError:
                return await ctx.send("FFmpeg is required to process videos/gifs, but it's not installed on this system.")
            finally:
                if os.path.exists(in_path):
                    os.remove(in_path)

        is_animated_img = False
        original_fmt = 'webp'
        if not is_video:
            try:
                img = Image.open(io.BytesIO(img_bytes))
                is_animated_img = getattr(img, "is_animated", False)
                original_fmt = img.format.lower() if img.format else 'webp'
            except:
                pass

        prompt_msg = None
        if is_animated_img:
            chosen_fmt = original_fmt
        else:
            embed = discord.Embed(
                description="Choose the format you want to convert\n"
                            "**Webp**: Better optimization, better quality, better for transparency image from PNG/APNG\n"
                            "**Gif**: Better legacy support, use this if you import a static image and Discord do detect this as an animated image"
            )
            prompt_view = InitialFormatSelectView(ctx)
            prompt_msg = await ctx.send(embed=embed, view=prompt_view)
            await prompt_view.wait()
            
            if not prompt_view.format_chosen:
                return
                
            chosen_fmt = prompt_view.format_chosen

        def convert_to_animated(b, target_fmt):
            try:
                img = Image.open(io.BytesIO(b))
                frames = []
                durations = []
                for frame in ImageSequence.Iterator(img):
                    f = frame.copy()
                    if f.mode != 'RGBA':
                        f = f.convert('RGBA')
                    frames.append(f)
                    durations.append(frame.info.get('duration', 100))
                
                out = io.BytesIO()
                fmt = target_fmt.upper()
                save_kwargs = {
                    'format': fmt,
                    'save_all': True,
                    'append_images': frames[1:],
                    'duration': durations,
                    'loop': img.info.get('loop', 0)
                }
                if fmt == 'WEBP':
                    save_kwargs['method'] = 6
                elif fmt == 'GIF':
                    save_kwargs['disposal'] = 2
                
                if len(frames) == 1:
                    frames.append(frames[0].copy())
                    durations.append(100)
                    save_kwargs['append_images'] = frames[1:]
                    save_kwargs['duration'] = durations
                    save_kwargs['save_all'] = True
                    save_kwargs['loop'] = 0
                    
                frames[0].save(out, **save_kwargs)
                return out.getvalue()
            except Exception as e:
                print(f"Error converting to {target_fmt} on import: {e}")
                return b

        if not (is_video and chosen_fmt == 'webp') and not is_animated_img:
            loop = asyncio.get_running_loop()
            img_bytes = await loop.run_in_executor(None, convert_to_animated, img_bytes, chosen_fmt)
        
        if len(img_bytes) > 25 * 1024 * 1024:
            msg_content = "The resulting file is too large to send (>25MB). Please try a shorter or lower resolution media."
            if prompt_msg:
                return await prompt_msg.edit(content=msg_content, embed=None, view=None)
            else:
                return await ctx.send(msg_content)
            
        view = GifMakerView(ctx, img_bytes, initial_format=chosen_fmt, is_video=is_video)
        file = discord.File(io.BytesIO(img_bytes), filename=f"output.{chosen_fmt}")
        if prompt_msg:
            await prompt_msg.delete()
        await ctx.send("Gif Maker loaded:", file=file, view=view)

async def setup(bot):
    await bot.add_cog(GifMakerCog(bot))
