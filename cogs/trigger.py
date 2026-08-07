import discord
from discord import app_commands
from discord.ext import commands
from core.data_manager import data_manager
from cogs.admin import is_admin_or_role
import re
import random
import uuid

def remove_vietnamese_accents(s: str) -> str:
    s = re.sub(r'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', s)
    s = re.sub(r'[ÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ]', 'A', s)
    s = re.sub(r'[èéẹẻẽêềếệểễ]', 'e', s)
    s = re.sub(r'[ÈÉẸẺẼÊỀẾỆỂỄ]', 'E', s)
    s = re.sub(r'[òóọỏõôồốộổỗơờớợởỡ]', 'o', s)
    s = re.sub(r'[ÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠ]', 'O', s)
    s = re.sub(r'[ìíịỉĩ]', 'i', s)
    s = re.sub(r'[ÌÍỊỈĨ]', 'I', s)
    s = re.sub(r'[ùúụủũưừứựửữ]', 'u', s)
    s = re.sub(r'[ÙÚỤỦŨƯỪỨỰỬỮ]', 'U', s)
    s = re.sub(r'[ỳýỵỷỹ]', 'y', s)
    s = re.sub(r'[ỲÝỴỶỸ]', 'Y', s)
    s = re.sub(r'[Đ]', 'D', s)
    s = re.sub(r'[đ]', 'd', s)
    return s

class TriggerPaginationView(discord.ui.View):
    def __init__(self, embeds: list[discord.Embed]):
        super().__init__(timeout=180)
        self.embeds = embeds
        self.current_page = 0
        self.update_buttons()

    def update_buttons(self):
        self.prev_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page == len(self.embeds) - 1

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary, custom_id="prev_page")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary, custom_id="next_page")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)


class Trigger(commands.GroupCog, group_name="trigger"):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    def migrate_triggers_if_needed(self, triggers: dict):
        migrated = False
        new_triggers = {}
        for key, data in triggers.items():
            if isinstance(data, dict) and "words" in data:
                new_triggers[key] = data
            else:
                # Old format
                migrated = True
                trigger_id = str(uuid.uuid4())
                if isinstance(data, dict):
                    resp = data.get("response", "")
                    reply = data.get("reply", False)
                else:
                    resp = data
                    reply = False
                new_triggers[trigger_id] = {
                    "words": [key.lower()],
                    "responses": [resp],
                    "reply": reply
                }
        return new_triggers, migrated

    @app_commands.command(name="add", description="Add a new auto-reply trigger for the server.")
    @app_commands.describe(
        word1="Trigger word 1", response1="Response 1", reply="True to reply to the user, False to send in channel.",
        word2="Trigger word 2", word3="Trigger word 3", word4="Trigger word 4", word5="Trigger word 5",
        response2="Response 2", response3="Response 3", response4="Response 4", response5="Response 5"
    )
    @app_commands.check(is_admin_or_role)
    async def trigger_add(
        self, interaction: discord.Interaction, reply: bool,
        word1: str, response1: str,
        word2: str = None, word3: str = None, word4: str = None, word5: str = None,
        response2: str = None, response3: str = None, response4: str = None, response5: str = None
    ):
        config = await data_manager.get_server_config(interaction.guild_id)
        triggers = config.get("triggers", {})
        
        triggers, migrated = self.migrate_triggers_if_needed(triggers)
        
        words = [w.lower() for w in [word1, word2, word3, word4, word5] if w]
        responses = [r for r in [response1, response2, response3, response4, response5] if r]
        
        trigger_id = str(uuid.uuid4())
        triggers[trigger_id] = {
            "words": words,
            "responses": responses,
            "reply": reply
        }
        
        await data_manager.set_server_config(interaction.guild_id, "triggers", triggers)
        reply_text = "Yes" if reply else "No"
        
        words_str = ", ".join([f"`{w}`" for w in words])
        await interaction.response.send_message(f"Added trigger for {words_str} => {len(responses)} response(s). (Reply: {reply_text})", ephemeral=True)

    @app_commands.command(name="remove", description="Remove an auto-reply trigger by providing any of its trigger words.")
    @app_commands.describe(word="A trigger word to remove the entire associated trigger group.")
    @app_commands.check(is_admin_or_role)
    async def trigger_remove(self, interaction: discord.Interaction, word: str):
        config = await data_manager.get_server_config(interaction.guild_id)
        triggers = config.get("triggers", {})
        
        triggers, migrated = self.migrate_triggers_if_needed(triggers)
        
        word_lower = word.lower()
        found_id = None
        for t_id, data in triggers.items():
            if word_lower in data["words"]:
                found_id = t_id
                break
                
        if found_id:
            del triggers[found_id]
            await data_manager.set_server_config(interaction.guild_id, "triggers", triggers)
            await interaction.response.send_message(f"Removed trigger group containing the word `{word}`.", ephemeral=True)
        else:
            if migrated:
                await data_manager.set_server_config(interaction.guild_id, "triggers", triggers)
            await interaction.response.send_message(f"No trigger found containing the word `{word}`.", ephemeral=True)

    @app_commands.command(name="list", description="List all auto-reply triggers.")
    @app_commands.check(is_admin_or_role)
    async def trigger_list(self, interaction: discord.Interaction):
        config = await data_manager.get_server_config(interaction.guild_id)
        triggers = config.get("triggers", {})
        
        triggers, migrated = self.migrate_triggers_if_needed(triggers)
        if migrated:
            await data_manager.set_server_config(interaction.guild_id, "triggers", triggers)
        
        if not triggers:
            return await interaction.response.send_message("No triggers configured for this server.", ephemeral=True)
            
        lines = []
        for t_id, data in triggers.items():
            words_str = ", ".join(data["words"])
            resp_count = len(data["responses"])
            reply_str = " (Reply: Yes)" if data.get("reply", False) else ""
            
            lines.append(f"**{words_str}** => {resp_count} response(s){reply_str}")
            
        # Pagination
        items_per_page = 15
        embeds = []
        for i in range(0, len(lines), items_per_page):
            chunk = lines[i:i + items_per_page]
            embed = discord.Embed(title="Auto-reply Triggers", description="\n".join(chunk), color=discord.Color.blurple())
            page_num = (i // items_per_page) + 1
            total_pages = (len(lines) + items_per_page - 1) // items_per_page
            embed.set_footer(text=f"Page {page_num} of {total_pages}")
            embeds.append(embed)
            
        if len(embeds) == 1:
            await interaction.response.send_message(embed=embeds[0], ephemeral=True)
        else:
            view = TriggerPaginationView(embeds)
            await interaction.response.send_message(embed=embeds[0], view=view, ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        config = await data_manager.get_server_config(message.guild.id)
        triggers = config.get("triggers", {})
        if not triggers:
            return

        triggers, _ = self.migrate_triggers_if_needed(triggers)

        # Normalize message content
        content_normalized = remove_vietnamese_accents(message.content).lower()
        
        for t_id, data in triggers.items():
            words = data.get("words", [])
            matched = False
            for word in words:
                word_normalized = remove_vietnamese_accents(word).lower()
                escaped_word = re.escape(word_normalized)
                pattern = r'\b' + escaped_word + r'\b'
                if re.search(pattern, content_normalized):
                    matched = True
                    break
                    
            if matched:
                responses = data.get("responses", [])
                if responses:
                    response_text = random.choice(responses)
                    should_reply = data.get("reply", False)
                    
                    if should_reply:
                        await message.reply(response_text)
                    else:
                        await message.channel.send(response_text)
                    break

async def setup(bot):
    await bot.add_cog(Trigger(bot))
