import os
import shutil
import sys
from cryptography.fernet import Fernet
import asyncio
import json

# Setup env
if not os.path.exists(".env"):
    if os.path.exists(".env.example"):
        shutil.copy(".env.example", ".env")
    else:
        with open(".env", "w") as f:
            f.write("DISCORD_TOKEN=YOUR.TOKEN.GOES.HERE\n")
            f.write("ENCRYPTION_KEY=YOUR.ENCRYPTION.KEY.HERE\n")

# Generate and set key
key = Fernet.generate_key().decode()
with open(".env", "r") as f:
    content = f.read()

if "ENCRYPTION_KEY=YOUR.ENCRYPTION.KEY.HERE" in content:
    content = content.replace("ENCRYPTION_KEY=YOUR.ENCRYPTION.KEY.HERE", f"ENCRYPTION_KEY={key}")
elif "ENCRYPTION_KEY=" not in content:
    content += f"\nENCRYPTION_KEY={key}\n"
else:
    # Key already exists
    pass

with open(".env", "w") as f:
    f.write(content)

print(f"Set ENCRYPTION_KEY in .env")

# Now import data_manager
from core.data_manager import data_manager

async def test():
    # Write some data
    await data_manager.set_server_config(12345, "test_key", "test_value")
    config = await data_manager.get_server_config(12345)
    print("Config retrieved:", config)
    assert config.get("test_key") == "test_value"
    
    # Write noichu data
    state = await data_manager.get_noichu_state(12345)
    state["last_word"] = "apple"
    await data_manager.save_noichu_state(12345, state)
    
    state_loaded = await data_manager.get_noichu_state(12345)
    print("Noichu retrieved:", state_loaded)
    assert state_loaded.get("last_word") == "apple"
    
    print("All tests passed.")
    
    # Check if files exist
    assert os.path.exists("data/servers_config.enc")
    assert os.path.exists("data/noichu_progress.json")
    
    # Check if we can read noichu in plain text
    with open("data/noichu_progress.json", "r", encoding="utf-8") as f:
        noichu_raw = json.load(f)
    print("Raw noichu file:", noichu_raw)
    assert noichu_raw["12345"]["last_word"] == "apple"

asyncio.run(test())
