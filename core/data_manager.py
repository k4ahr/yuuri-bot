import json
import os
import asyncio
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

class DataManager:
    def __init__(self, config_filepath="data/servers_config.enc", noichu_filepath="data/noichu_progress.json", users_config_filepath="data/users_config.enc"):
        self.config_filepath = config_filepath
        self.noichu_filepath = noichu_filepath
        self.users_config_filepath = users_config_filepath
        self.config_lock = asyncio.Lock()
        self.noichu_lock = asyncio.Lock()
        self.users_lock = asyncio.Lock()
        
        self.encryption_key = os.getenv("ENCRYPTION_KEY")
        if self.encryption_key:
            try:
                self.fernet = Fernet(self.encryption_key.encode())
            except Exception as e:
                self.fernet = None
                print(f"WARNING: Invalid ENCRYPTION_KEY: {e}")
        else:
            self.fernet = None
            print("WARNING: ENCRYPTION_KEY not found in environment variables. Configuration will not be loaded or saved correctly if encryption is required.")

        self._ensure_files()

    def _ensure_files(self):
        os.makedirs(os.path.dirname(self.config_filepath), exist_ok=True)
        
        # Check for legacy file migration
        legacy_file = "data/servers.json"
        if os.path.exists(legacy_file) and not os.path.exists(self.config_filepath):
            self._migrate_legacy_data(legacy_file)

        if not os.path.exists(self.config_filepath):
            self._write_encrypted_config({})
            
        if not os.path.exists(self.users_config_filepath):
            self._write_encrypted_users_config({})
        
        if not os.path.exists(self.noichu_filepath):
            with open(self.noichu_filepath, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def _migrate_legacy_data(self, legacy_file):
        print("Migrating legacy servers.json data...")
        try:
            with open(legacy_file, "r", encoding="utf-8") as f:
                legacy_data = json.load(f)
            
            config_data = {}
            noichu_data = {}
            
            for guild_id, data in legacy_data.items():
                if "noichu" in data:
                    noichu_data[guild_id] = data.pop("noichu")
                if data:
                    config_data[guild_id] = data
            
            # Save separated data
            self._write_encrypted_config(config_data)
            
            with open(self.noichu_filepath, "w", encoding="utf-8") as f:
                json.dump(noichu_data, f, indent=4, ensure_ascii=False)
            
            # Backup legacy file
            os.rename(legacy_file, legacy_file + ".bak")
            print("Migration successful. Old data backed up to servers.json.bak")
        except Exception as e:
            print(f"Error during migration: {e}")

    def _read_encrypted(self, filepath):
        if not self.fernet:
            return {}
        try:
            with open(filepath, "rb") as f:
                encrypted_data = f.read()
            if not encrypted_data:
                return {}
            decrypted_data = self.fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode('utf-8'))
        except FileNotFoundError:
            return {}
        except Exception as e:
            print(f"Error reading encrypted config {filepath}: {e}")
            return {}

    def _write_encrypted(self, filepath, data):
        if not self.fernet:
            print(f"WARNING: Cannot save config {filepath}, ENCRYPTION_KEY missing.")
            return
        try:
            json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
            encrypted_data = self.fernet.encrypt(json_data)
            with open(filepath, "wb") as f:
                f.write(encrypted_data)
        except Exception as e:
            print(f"Error writing encrypted config {filepath}: {e}")

    def _read_encrypted_config(self):
        return self._read_encrypted(self.config_filepath)

    def _write_encrypted_config(self, data):
        self._write_encrypted(self.config_filepath, data)
        
    def _read_encrypted_users_config(self):
        return self._read_encrypted(self.users_config_filepath)

    def _write_encrypted_users_config(self, data):
        self._write_encrypted(self.users_config_filepath, data)

    async def get_server_config(self, guild_id):
        async with self.config_lock:
            data = self._read_encrypted_config()
            return data.get(str(guild_id), {})

    async def set_server_config(self, guild_id, key, value):
        async with self.config_lock:
            data = self._read_encrypted_config()
            guild_str = str(guild_id)
            if guild_str not in data:
                data[guild_str] = {}
            data[guild_str][key] = value
            self._write_encrypted_config(data)

    async def get_user_data(self, user_id):
        async with self.users_lock:
            data = self._read_encrypted_users_config()
            return data.get(str(user_id), {})

    async def set_user_data(self, user_id, key, value):
        async with self.users_lock:
            data = self._read_encrypted_users_config()
            user_str = str(user_id)
            if user_str not in data:
                data[user_str] = {}
            data[user_str][key] = value
            self._write_encrypted_users_config(data)
            
    async def remove_user_data(self, user_id, key):
        async with self.users_lock:
            data = self._read_encrypted_users_config()
            user_str = str(user_id)
            if user_str in data and key in data[user_str]:
                del data[user_str][key]
                self._write_encrypted_users_config(data)

    def encrypt_string(self, text: str) -> str:
        if not self.fernet:
            return text
        return self.fernet.encrypt(text.encode('utf-8')).decode('utf-8')

    def decrypt_string(self, encrypted_text: str) -> str:
        if not self.fernet:
            return encrypted_text
        try:
            return self.fernet.decrypt(encrypted_text.encode('utf-8')).decode('utf-8')
        except Exception:
            return ""

    async def load_noichu_data(self):
        async with self.noichu_lock:
            try:
                with open(self.noichu_filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                return {}

    async def save_noichu_data(self, data):
        async with self.noichu_lock:
            with open(self.noichu_filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

    async def get_noichu_state(self, guild_id):
        data = await self.load_noichu_data()
        guild_str = str(guild_id)
        default_state = {
            "channel_id": None,
            "last_word": None,
            "used_words_list": [],
            "last_author_id": None,
            "leaderboard": {}
        }
        return data.get(guild_str, default_state)

    async def save_noichu_state(self, guild_id, state):
        data = await self.load_noichu_data()
        data[str(guild_id)] = state
        await self.save_noichu_data(data)

# Singleton instance
data_manager = DataManager()
