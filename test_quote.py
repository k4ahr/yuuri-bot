import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import textwrap

def create_quote_image(avatar_path, text, username, output_path):
    # 16:9 canvas
    width, height = 1920, 1080
    
    # Create base black image
    base = Image.new("RGB", (width, height), "black")
    
    # Load and resize avatar to fit height (1080x1080)
    try:
        avatar = Image.open(avatar_path).convert("RGBA")
        avatar = avatar.resize((height, height), Image.Resampling.LANCZOS)
    except Exception as e:
        print(f"Failed to load avatar: {e}")
        return
        
    # Create a gradient mask for fading the avatar
    # Avatar is on the left. We want it to fade into black on the right.
    # The avatar is from x=0 to x=1080.
    # Let's make it start fading at x=500 and fully fade out by x=1080.
    mask = Image.new("L", (height, height), 255)
    draw = ImageDraw.Draw(mask)
    fade_start = 500
    fade_end = 1080
    for x in range(fade_start, fade_end):
        alpha = int(255 - (x - fade_start) / (fade_end - fade_start) * 255)
        draw.line([(x, 0), (x, height)], fill=alpha)
        
    # Apply mask to avatar
    avatar.putalpha(mask)
    
    # Paste avatar onto base
    base.paste(avatar, (0, 0), avatar)
    
    # Now draw the text on the right side.
    # Available area: x=1080 to x=1920 (width 840), but we can start earlier since it's faded, maybe x=900 to x=1800.
    # Let's say text box is x=960 to 1820 (width 860). Center of text box is x=1390.
    draw = ImageDraw.Draw(base)
    
    # Fallback fonts
    try:
        font_large = ImageFont.truetype("arial.ttf", 60)
        font_small = ImageFont.truetype("arial.ttf", 40)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
        
    # Wrap text
    wrapper = textwrap.TextWrapper(width=30)
    wrapped_text = wrapper.wrap(f'"{text}"')
    
    # Calculate text height
    line_spacing = 20
    text_height = sum([font_large.getbbox(line)[3] - font_large.getbbox(line)[1] for line in wrapped_text]) + (len(wrapped_text) - 1) * line_spacing
    
    # Add username height
    user_text = f"- {username}"
    user_height = font_small.getbbox(user_text)[3] - font_small.getbbox(user_text)[1]
    
    total_height = text_height + 40 + user_height
    
    # Starting Y position
    start_y = (height - total_height) // 2
    
    current_y = start_y
    for line in wrapped_text:
        bbox = font_large.getbbox(line)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = 960 + (860 - w) // 2
        draw.text((x, current_y), line, font=font_large, fill="white")
        current_y += h + line_spacing
        
    current_y += 40 - line_spacing
    bbox = font_small.getbbox(user_text)
    w = bbox[2] - bbox[0]
    x = 960 + (860 - w) // 2
    draw.text((x, current_y), user_text, font=font_small, fill="gray")
    
    base.save(output_path)
    print(f"Saved {output_path}")

if __name__ == "__main__":
    # Create a dummy avatar
    dummy = Image.new("RGB", (1080, 1080), "blue")
    dummy.save("dummy_avatar.png")
    create_quote_image("dummy_avatar.png", "This is a beautiful quote that spans multiple lines and shows how the text wrapping works.", "Albert Einstein", "test_quote.png")
