import discord
from discord import app_commands
from discord.ext import commands
from core.data_manager import data_manager
from cogs.admin import is_admin_or_role
import re
import random
import uuid
import copy

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


class TriggerAddModal(discord.ui.Modal, title='Add New Trigger'):
    words = discord.ui.TextInput(
        label='Trigger Words (comma separated)',
        style=discord.TextStyle.short,
        placeholder='Enter words separated by commas.',
        required=True
    )
    responses = discord.ui.TextInput(
        label='Responses (one per line)',
        style=discord.TextStyle.paragraph,
        placeholder='Enter responses, one per line. Use \\run!command (e.g. \\run!help) to run bot commands.',
        required=True
    )
    whitelist = discord.ui.TextInput(
        label='Whitelist (Optional)',
        style=discord.TextStyle.short,
        placeholder='Optional: @User or @Role or IDs, comma separated.',
        required=False
    )
    blacklist = discord.ui.TextInput(
        label='Blacklist (Optional)',
        style=discord.TextStyle.short,
        placeholder='Optional: @User or @Role or IDs, comma separated.',
        required=False
    )

    def __init__(self, cog, reply: bool):
        super().__init__()
        self.cog = cog
        self.reply = reply

    async def on_submit(self, interaction: discord.Interaction):
        config = await data_manager.get_server_config(interaction.guild_id)
        triggers = config.get("triggers", {})
        
        triggers, migrated = self.cog.migrate_triggers_if_needed(triggers)
        
        # Parse inputs
        words_list = [w.strip().lower() for w in self.words.value.split(',') if w.strip()]
        responses_list = [r.strip() for r in self.responses.value.split('\n') if r.strip()]
        
        # Helper to extract IDs
        def extract_ids(text):
            if not text:
                return []
            return re.findall(r'\d{15,20}', text)

        whitelist_ids = extract_ids(self.whitelist.value)
        blacklist_ids = extract_ids(self.blacklist.value)
        
        if not words_list:
            return await interaction.response.send_message("You must provide at least one trigger word.", ephemeral=True)
            
        if not responses_list:
            return await interaction.response.send_message("You must provide at least one response.", ephemeral=True)
            
        words_key = tuple(sorted(words_list))
        existing_id = None
        for t_id, data in triggers.items():
            if tuple(sorted([w.lower() for w in data.get("words", [])])) == words_key:
                existing_id = t_id
                break
                
        if existing_id:
            for resp in responses_list:
                if resp not in triggers[existing_id]["responses"]:
                    triggers[existing_id]["responses"].append(resp)
            if whitelist_ids:
                existing_wl = triggers[existing_id].setdefault("whitelist", [])
                for w in whitelist_ids:
                    if w not in existing_wl:
                        existing_wl.append(w)
            if blacklist_ids:
                existing_bl = triggers[existing_id].setdefault("blacklist", [])
                for b in blacklist_ids:
                    if b not in existing_bl:
                        existing_bl.append(b)
            # Update reply preference to newest
            triggers[existing_id]["reply"] = self.reply
        else:
            trigger_id = str(uuid.uuid4())
            triggers[trigger_id] = {
                "words": words_list,
                "responses": responses_list,
                "reply": self.reply
            }
            if whitelist_ids:
                triggers[trigger_id]["whitelist"] = whitelist_ids
            if blacklist_ids:
                triggers[trigger_id]["blacklist"] = blacklist_ids
            
        await data_manager.set_server_config(interaction.guild_id, "triggers", triggers)
        
        reply_text = "Yes" if self.reply else "No"
        words_str = ", ".join([f"`{w}`" for w in words_list])
        
        msg = f"Added/Merged trigger for {words_str} => {len(responses_list)} new response(s). (Reply: {reply_text})"
        if whitelist_ids:
            msg += f"\n**Whitelist:** {len(whitelist_ids)} entries"
        if blacklist_ids:
            msg += f"\n**Blacklist:** {len(blacklist_ids)} entries"
            
        await interaction.response.send_message(msg, ephemeral=True)



class Trigger(commands.GroupCog, group_name="trigger", group_description="Manage auto-reply triggers."):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    async def cog_load(self):
        # Run migration on all servers in the background when the cog loads
        import asyncio
        asyncio.create_task(self.run_global_migration())

    async def run_global_migration(self):
        import logging
        logger = logging.getLogger('discord')
        
        async with data_manager.config_lock:
            data = await data_manager._read_encrypted_config()
            changed = False
            for guild_id, guild_data in data.items():
                triggers = guild_data.get("triggers", {})
                if not triggers:
                    continue
                merged_triggers, migrated = self.migrate_triggers_if_needed(triggers)
                if migrated:
                    guild_data["triggers"] = merged_triggers
                    changed = True
            
            if changed:
                await data_manager._write_encrypted_config(data)
                logger.info("Global trigger migration completed and saved successfully.")

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
                
        # Deduplication / Merging step
        merged_triggers = {}
        words_to_uuid = {}
        
        for t_id, data in new_triggers.items():
            words_key = tuple(sorted([w.lower() for w in data.get("words", [])]))
            
            if words_key in words_to_uuid:
                migrated = True
                existing_id = words_to_uuid[words_key]
                existing_data = merged_triggers[existing_id]
                
                for resp in data.get("responses", []):
                    if resp not in existing_data["responses"]:
                        existing_data["responses"].append(resp)
            else:
                words_to_uuid[words_key] = t_id
                merged_triggers[t_id] = data
                
        return merged_triggers, migrated

    @app_commands.command(name="add", description="Add a new auto-reply trigger for the server.")
    @app_commands.describe(reply="True to reply to the user, False to send in channel.")
    @app_commands.check(is_admin_or_role)
    async def trigger_add(self, interaction: discord.Interaction, reply: bool):
        modal = TriggerAddModal(self, reply)
        await interaction.response.send_modal(modal)

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
        content_normalized = message.content.lower()
        
        for t_id, data in triggers.items():
            whitelist = data.get("whitelist", [])
            blacklist = data.get("blacklist", [])
            
            if whitelist or blacklist:
                author_ids = [str(message.author.id)] + [str(role.id) for role in getattr(message.author, 'roles', [])]
                
                if whitelist and not any(w_id in author_ids for w_id in whitelist):
                    continue
                    
                if blacklist and any(b_id in author_ids for b_id in blacklist):
                    continue

            words = data.get("words", [])
            matched = False
            for word in words:
                word_normalized = word.lower()
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
                    
                    # Check if response is a command execution prefix (\run! or /run!)
                    if response_text.startswith(("\\run!", "/run!")):
                        prefix_len = len("\\run!") if response_text.startswith("\\run!") else len("/run!")
                        raw_command = response_text[prefix_len:].strip()
                        if raw_command.startswith(("y!", "Y!")):
                            raw_command = raw_command[2:].strip()
                        elif raw_command.startswith("/"):
                            raw_command = raw_command[1:].strip()

                        # Clone message with simulated command content
                        new_message = copy.copy(message)
                        new_message.content = f"y!{raw_command}"
                        
                        ctx = await self.bot.get_context(new_message)
                        if ctx.command:
                            if should_reply:
                                orig_send = ctx.send
                                async def send_with_reply(*args, **kwargs):
                                    kwargs.setdefault('reference', message.to_reference(fail_if_not_exists=False))
                                    kwargs.setdefault('mention_author', False)
                                    return await orig_send(*args, **kwargs)
                                ctx.send = send_with_reply

                            try:
                                await self.bot.invoke(ctx)
                            except Exception as e:
                                error_msg = f"Error running command `{raw_command}`: {e}"
                                if should_reply:
                                    await message.reply(error_msg)
                                else:
                                    await message.channel.send(error_msg)
                        else:
                            error_msg = f"Command `{raw_command}` not found."
                            if should_reply:
                                await message.reply(error_msg)
                            else:
                                await message.channel.send(error_msg)
                    else:
                        if should_reply:
                            await message.reply(response_text)
                        else:
                            await message.channel.send(response_text)
                    break

async def setup(bot):
    await bot.add_cog(Trigger(bot))
