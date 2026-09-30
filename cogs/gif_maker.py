import discord
from discord.ext import commands
import io
import os
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageSequence
import asyncio

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
            discord.SelectOption(label="Convert to GIF & optimize", value="to_gif", description="Convert to .GIF format"),
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
                try:
                    bubble = Image.open("assets/images/bubble.png").convert("RGBA")
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
                    new_f = Image.new('RGBA', (f.width, f.height + b.height), (255, 255, 255, 0))
                    new_f.paste(b, (0, 0))
                    new_f.paste(f, (0, b.height))
                    f = new_f
                    
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
                    
                    new_f = Image.new('RGBA', (f.width, f.height + text_box_height), (255, 255, 255, 255))
                    new_f.paste(f, (0, text_box_height))
                    
                    d = ImageDraw.Draw(new_f)
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
            
            if action in ["optimize", "to_gif"]:
                save_kwargs['optimize'] = True
                
            if action == "to_gif":
                self.current_format = 'gif'
                
            format_to_save = 'GIF' if self.current_format == 'gif' else 'WEBP'
            if format_to_save == 'WEBP':
                save_kwargs['method'] = 6
                if 'optimize' in save_kwargs:
                    del save_kwargs['optimize']
                    
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
                
        if not attachment:
            return await ctx.send("Please attach an image/video or reply to a message containing one.")
            
        is_video = False
        if attachment.content_type and attachment.content_type.startswith('video/'):
            is_video = True
                
        img_bytes = await attachment.read()
        
        if is_video:
            import tempfile
            import subprocess
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_in:
                temp_in.write(img_bytes)
                in_path = temp_in.name
                
            out_path = in_path + ".gif"
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
                    if duration > 15.5:
                        os.remove(in_path)
                        return await ctx.send(f"Video is too long! Your video is {duration:.1f}s, but the maximum allowed length is 15 seconds.")
                except ValueError:
                    pass

                proc = await asyncio.create_subprocess_exec(
                    'ffmpeg', '-y', '-i', in_path, '-t', '15', '-vf', 'scale=480:-1,fps=15', out_path,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL
                )
                await proc.communicate()
                if os.path.exists(out_path):
                    with open(out_path, 'rb') as f:
                        img_bytes = f.read()
                    os.remove(out_path)
                else:
                    return await ctx.send("Failed to process video. FFmpeg might not be installed or failed.")
            except FileNotFoundError:
                return await ctx.send("FFmpeg is required to process videos, but it's not installed on this system.")
            finally:
                if os.path.exists(in_path):
                    os.remove(in_path)

        def convert_to_animated(b, is_vid):
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
                fmt = 'WEBP' if is_vid else 'GIF'
                save_kwargs = {
                    'format': fmt,
                    'save_all': True,
                    'append_images': frames[1:],
                    'duration': durations,
                    'loop': img.info.get('loop', 0)
                }
                if fmt == 'WEBP':
                    save_kwargs['method'] = 6
                
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
                print(f"Error converting to gif on import: {e}")
                return b

        loop = asyncio.get_running_loop()
        img_bytes = await loop.run_in_executor(None, convert_to_animated, img_bytes, is_video)
        
        if len(img_bytes) > 25 * 1024 * 1024:
            return await ctx.send("The resulting file is too large to send (>25MB). Please try a shorter or lower resolution video.")
            
        initial_fmt = 'webp' if is_video else 'gif'
        view = GifMakerView(ctx, img_bytes, initial_format=initial_fmt, is_video=is_video)
        file = discord.File(io.BytesIO(img_bytes), filename=f"output.{initial_fmt}")
        await ctx.send("Gif Maker loaded:", file=file, view=view)

async def setup(bot):
    await bot.add_cog(GifMakerCog(bot))
