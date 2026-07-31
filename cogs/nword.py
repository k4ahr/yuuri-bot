import discord
from discord import app_commands
from discord.ext import commands
import re
from collections import defaultdict

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
            lines.append(f"**#{i}** <@{user_id}>: {count} times")
            
        embed.description = "\n".join(lines)
        embed.set_footer(text=f"Page {self.current_page + 1}/{self.max_pages}")
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
        # We defer the response because scanning message history takes a long time
        await interaction.response.defer(thinking=True)
        
        if not TARGET_WORDS:
            return await interaction.followup.send("No target words are hardcoded in the bot.")
            
        counts = defaultdict(int)
        
        # Compile a regex to find all hardcoded words (case-insensitive)
        patterns = [re.escape(w.lower()) for w in TARGET_WORDS]
        regex = re.compile(r'\b(' + '|'.join(patterns) + r')\b', re.IGNORECASE)
        
        scanned_messages = 0
        
        # Scan all text channels in the guild
        for channel in interaction.guild.text_channels:
            try:
                # Limit to 5000 messages per channel to prevent the bot from hanging indefinitely on huge servers
                async for message in channel.history(limit=5000):
                    scanned_messages += 1
                    if message.author.bot:
                        continue
                        
                    matches = regex.findall(message.content)
                    if matches:
                        counts[message.author.id] += len(matches)
            except (discord.Forbidden, discord.HTTPException):
                continue
                
        if not counts:
            return await interaction.followup.send(f"Scanned {scanned_messages} recent messages. No one has said the target words!")
            
        # Sort data
        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        
        title = f"Word Leaderboard"
        view = NWordView(interaction, sorted_counts, title)
        embed = view.generate_embed()
        
        await interaction.followup.send(
            content=f"*(Scanned {scanned_messages} recent messages across all channels)*\n**Target Words:** {', '.join(TARGET_WORDS)}", 
            embed=embed, 
            view=view
        )

async def setup(bot):
    await bot.add_cog(NWord(bot))
