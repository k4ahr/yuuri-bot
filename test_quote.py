import os
from PIL import Image
import io
import asyncio
from cogs.quote import Quote

def test_quote():
    # Create a dummy avatar as bytes
    dummy = Image.new("RGB", (1080, 1080), "blue")
    buffer = io.BytesIO()
    dummy.save(buffer, format="PNG")
    avatar_bytes = buffer.getvalue()

    class MockBot:
        class MockTree:
            def add_command(self, cmd): pass
        tree = MockTree()
    
    cog = Quote(MockBot())
    
    text = "Hello __underline__ and ~~strikethrough~~ and ||spoiler|| and `code` and\n```python\nprint('hello')\n```"
    # Make the text very long to trigger scaling
    text = (text + " ") * 20
    username = "Albert Einstein"
    
    print("Generating quote...")
    img_buffer = cog.generate_quote_image(avatar_bytes, text, username)
    if img_buffer:
        with open("test_quote.png", "wb") as f:
            f.write(img_buffer.read())
        print("Saved to test_quote.png")
    else:
        print("Failed to generate quote image.")

if __name__ == "__main__":
    test_quote()
