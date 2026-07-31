import discord
from discord import app_commands
from discord.ext import commands
import re
from collections import defaultdict
from core.data_manager import data_manager
from datetime import datetime, timezone

# =====================================================================
# EDIT THIS LIST TO CHANGE THE WORDS YOU WANT TO SEARCH FOR
# This list applies to all servers.
TARGET_WORDS = ["nigga", "nigger", "niggas" , "niggers", "ngga", "n1gga" , "n199a"]
# =====================================================================

class NWordView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, data: list, title: str):
        super().__init__(timeout=300)
        self.interaction = interaction
        self.data = data
        self.title = title
        self.current_page = 0
        self.per_page = 10
        self.max_pages = max(1, (len(data) + self.per_page - 1) // self.per_page)
        self.update_buttons()

    def update_buttons(self):
        self.prev_btn.disabled = self.current_page == 0
        self.next_btn.disabled = self.current_page >= self.max_pages - 1

    def generate_embed(self):
        embed = discord.Embed(title=self.title, color=discord.Color.gold())
        
        start = self.current_page * self.per_page
        end = start + self.per_page
        page_data = self.data[start:end]

        if not page_data:
            embed.description = "No results found."
            return embed

        lines = []
        for i, (user_id, count) in enumerate(page_data, start=start + 1):
            lines.append(f"**#{i}** <@{user_id}>: Said the nword {count} times")
            
        embed.description = "\n".join(lines)
        
        last_updated = self.data.get('last_updated') if isinstance(self.data, dict) else None
        
        if last_updated:
            # Format timestamp nicely
            try:
                dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                ts_str = f" • Last Scan: <t:{int(dt.timestamp())}:R>"
            except ValueError:
                ts_str = ""
        else:
            ts_str = ""
            
        embed.set_footer(text=f"Page {self.current_page + 1}/{self.max_pages}{ts_str}")
        return embed

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary, custom_id="prev")
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary, custom_id="next")
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)

class NWord(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="nword", description="HOW MANY NIGGAS DID YOU SAID?.")
    async def wordlb(self, interaction: discord.Interaction):
        config = await data_manager.get_server_config(interaction.guild_id)
        cached_data = config.get("nword_cache", {})
        
        if not cached_data.get("last_updated"):
            # First time scan, might take a while. Run in background.
            await interaction.response.send_message("Scanning messages in the background... I will ping you when it's done!", ephemeral=False)
            self.bot.loop.create_task(self.run_scan(interaction, first_time=True))
        else:
            # Subsequent scans are fast because of caching. Just defer and wait.
            await interaction.response.defer(thinking=True)
            await self.run_scan(interaction, first_time=False)
        
    async def run_scan(self, interaction: discord.Interaction, first_time: bool):
        if not TARGET_WORDS:
            msg = "Thankfully this server is racism free."
            if first_time:
                await interaction.channel.send(f"{interaction.user.mention} {msg}")
            else:
                await interaction.followup.send(msg)
            return
            
        config = await data_manager.get_server_config(interaction.guild_id)
        cached_data = config.get("nword_cache", {})
        
        # 'counts' dictionary is keyed by str user_ids
        counts = defaultdict(int)
        if "counts" in cached_data:
            for uid, cnt in cached_data["counts"].items():
                counts[str(uid)] = cnt
                
        last_updated_str = cached_data.get("last_updated")
        after_date = None
        if last_updated_str:
            try:
                after_date = datetime.fromisoformat(last_updated_str.replace('Z', '+00:00'))
            except ValueError:
                pass
                
        # Compile a regex to find all hardcoded words (case-insensitive)
        patterns = [re.escape(w.lower()) for w in TARGET_WORDS]
        regex = re.compile(r'\b(' + '|'.join(patterns) + r')\b', re.IGNORECASE)
        
        scanned_messages = 0
        new_matches_found = False
        
        # Scan all text channels in the guild
        for channel in interaction.guild.text_channels:
            try:
                # Lower limit to 1000 so the background task doesn't take forever, 
                # but relies heavily on the caching mechanism over time.
                async for message in channel.history(limit=1000, after=after_date):
                    scanned_messages += 1
                    if message.author.bot:
                        continue
                        
                    matches = regex.findall(message.content)
                    if matches:
                        counts[str(message.author.id)] += len(matches)
                        new_matches_found = True
            except (discord.Forbidden, discord.HTTPException):
                continue
                
        # Save updated cache if we found new messages
        now = discord.utils.utcnow()
        if new_matches_found or not last_updated_str:
            new_cache = {
                "counts": dict(counts),
                "last_updated": now.isoformat()
            }
            await data_manager.set_server_config(interaction.guild_id, "nword_cache", new_cache)
            
        if not counts:
            msg = f"Scanned {scanned_messages} recent messages. No one has said it recently!"
            if first_time:
                await interaction.channel.send(f"{interaction.user.mention} {msg}")
            else:
                await interaction.followup.send(msg)
            return
            
        # Sort data
        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        
        # In order to pass last_updated down to the view
        class DataWrapper(list):
            def __init__(self, data, last_updated):
                super().__init__(data)
                self.last_updated = last_updated
                
            def get(self, key):
                if key == 'last_updated':
                    return self.last_updated
                return None
                
        wrapped_data = DataWrapper(sorted_counts, now.isoformat())
        
        title = f"LIST OF THESE RACIST NIGGAS:"
        view = NWordView(interaction, wrapped_data, title)
        embed = view.generate_embed()
        
        if first_time:
            # Send the final result pinging the user
            await interaction.channel.send(
                content=f"{interaction.user.mention} The scan is complete!",
                embed=embed, 
                view=view
            )
        else:
            # Respond to the deferred slash command
            await interaction.followup.send(
                embed=embed,
                view=view
            )

async def setup(bot):
    await bot.add_cog(NWord(bot))
