import json
import os
import asyncio

class DataManager:
    def __init__(self, filepath="data/servers.json"):
        self.filepath = filepath
        self.lock = asyncio.Lock()
        self._ensure_file()

    def _ensure_file(self):
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        if not os.path.exists(self.filepath):
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump({}, f)

    async def load_data(self):
        async with self.lock:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)

    async def save_data(self, data):
        async with self.lock:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

    async def get_server_config(self, guild_id):
        data = await self.load_data()
        return data.get(str(guild_id), {})

    async def set_server_config(self, guild_id, key, value):
        data = await self.load_data()
        guild_str = str(guild_id)
        if guild_str not in data:
            data[guild_str] = {}
        data[guild_str][key] = value
        await self.save_data(data)

    async def get_noichu_state(self, guild_id):
        config = await self.get_server_config(guild_id)
        default_state = {
            "channel_id": None,
            "last_word": None,
            "used_words_list": [],
            "last_author_id": None,
            "leaderboard": {}
        }
        return config.get("noichu", default_state)

    async def save_noichu_state(self, guild_id, state):
        await self.set_server_config(guild_id, "noichu", state)

# Singleton instance
data_manager = DataManager()
