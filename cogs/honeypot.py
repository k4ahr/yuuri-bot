import discord
from discord import app_commands
from discord.ext import commands
from core.data_manager import data_manager
from cogs.admin import is_admin_or_role

class Honeypot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="sethoneypot", description="Sets the honeypot channel for this server.")
    @app_commands.describe(channel="The honeypot text channel.")
    @app_commands.check(is_admin_or_role)
    async def set_honeypot(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await data_manager.set_server_config(interaction.guild_id, "honeypot_channel", channel.id)
        await interaction.response.send_message(f"Honeypot channel set to {channel.mention}. Anyone who posts there will be banned.", ephemeral=True)

    @app_commands.command(name="sethoneypotdm", description="Sets the DM message sent to users when they trigger the honeypot.")
    @app_commands.describe(message="The message to DM the user.")
    @app_commands.check(is_admin_or_role)
    async def set_honeypotdm(self, interaction: discord.Interaction, message: str):
        await data_manager.set_server_config(interaction.guild_id, "honeypot_dm", message)
        await interaction.response.send_message(f"Honeypot DM set to: `{message}`", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore bots and DMs
        if message.author.bot or not message.guild:
            return

        config = await data_manager.get_server_config(message.guild.id)
        honeypot_channel_id = config.get("honeypot_channel")

        if honeypot_channel_id and message.channel.id == honeypot_channel_id:
            # Prepare to log
            log_channel_id = config.get("log_channel_id")
            log_channel = message.guild.get_channel(log_channel_id) if log_channel_id else None
            
            # DM user
            dm_msg = config.get("honeypot_dm", "You have been banned for triggering a honeypot channel.")
            dm_success = False
            try:
                await message.author.send(dm_msg)
                dm_success = True
            except:
                pass
                
            # Ban user
            ban_success = False
            try:
                await message.guild.ban(message.author, reason="Triggered Honeypot Channel", delete_message_days=1)
                ban_success = True
            except discord.Forbidden:
                pass # Permission error will be noted in the log channel
            except discord.HTTPException:
                pass
                
            # Log it
            if log_channel:
                embed = discord.Embed(title="🍯 Honeypot Triggered", color=discord.Color.orange())
                embed.add_field(name="User", value=f"{message.author.mention} ({message.author.id})", inline=False)
                embed.add_field(name="DM Status", value="✅ Delivered" if dm_success else "❌ Failed (DMs Closed)", inline=True)
                embed.add_field(name="Ban Status", value="✅ Success" if ban_success else "❌ Failed (Check Permissions)", inline=True)
                await log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Honeypot(bot))
