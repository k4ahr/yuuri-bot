import discord
from discord import app_commands
from discord.ext import commands
from core.data_manager import data_manager

async def is_admin_or_role(interaction: discord.Interaction):
    if interaction.user.guild_permissions.administrator:
        return True
    
    config = await data_manager.get_server_config(interaction.guild_id)
    admin_role_id = config.get("admin_role_id")
    if admin_role_id:
        role = interaction.guild.get_role(admin_role_id)
        if role and role in interaction.user.roles:
            return True
            
    await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
    return False

async def is_supporter_or_admin(interaction: discord.Interaction):
    if interaction.user.guild_permissions.administrator:
        return True
    
    config = await data_manager.get_server_config(interaction.guild_id)
    admin_role_id = config.get("admin_role_id")
    if admin_role_id:
        role = interaction.guild.get_role(admin_role_id)
        if role and role in interaction.user.roles:
            return True
            
    supporter_role_id = config.get("supporter_role_id")
    if supporter_role_id:
        role = interaction.guild.get_role(supporter_role_id)
        if role and role in interaction.user.roles:
            return True
            
    await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
    return False

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setadminrole", description="Set a custom role that can use admin commands.")
    @app_commands.describe(role="The role to grant admin privileges to.")
    @app_commands.default_permissions(administrator=True)
    async def set_admin_role(self, interaction: discord.Interaction, role: discord.Role):
        await data_manager.set_server_config(interaction.guild_id, "admin_role_id", role.id)
        await interaction.response.send_message(f"Admin role set to {role.mention}.", ephemeral=True)

    @app_commands.command(name="setsupporterrole", description="Set a custom role that can use supporter commands like say.")
    @app_commands.describe(role="The role to grant supporter privileges to.")
    @app_commands.default_permissions(administrator=True)
    async def set_supporter_role(self, interaction: discord.Interaction, role: discord.Role):
        await data_manager.set_server_config(interaction.guild_id, "supporter_role_id", role.id)
        await interaction.response.send_message(f"Supporter role set to {role.mention}.", ephemeral=True)

    @app_commands.command(name="setlogchannel", description="Set the channel where bot logs will be sent.")
    @app_commands.describe(channel="The text channel for logs.")
    @app_commands.check(is_admin_or_role)
    async def set_log_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await data_manager.set_server_config(interaction.guild_id, "log_channel_id", channel.id)
        await interaction.response.send_message(f"Log channel set to {channel.mention}.", ephemeral=True)

    @app_commands.command(name="say", description="Send an anonymous message through the bot.")
    @app_commands.describe(message="The message to send.")
    @app_commands.check(is_supporter_or_admin)
    async def say_command(self, interaction: discord.Interaction, message: str):
        await interaction.response.send_message("Message sent!", ephemeral=True)
        await interaction.channel.send(message)
        
        config = await data_manager.get_server_config(interaction.guild_id)
        log_channel_id = config.get("log_channel_id")
        if log_channel_id:
            log_channel = interaction.guild.get_channel(log_channel_id)
            if log_channel:
                embed = discord.Embed(title="Anonymous Say Log", color=discord.Color.red())
                embed.add_field(name="User", value=interaction.user.mention, inline=True)
                embed.add_field(name="Channel", value=interaction.channel.mention, inline=True)
                embed.add_field(name="Message", value=message, inline=False)
                await log_channel.send(embed=embed)

    @app_commands.command(name="addresponse", description="Add a random response when the bot is mentioned.")
    @app_commands.describe(response="The text to add.")
    @app_commands.check(is_admin_or_role)
    async def add_response(self, interaction: discord.Interaction, response: str):
        config = await data_manager.get_server_config(interaction.guild_id)
        responses = config.get("mention_responses", [])
        responses.append(response)
        await data_manager.set_server_config(interaction.guild_id, "mention_responses", responses)
        await interaction.response.send_message(f"Added response: `{response}`", ephemeral=True)

    @app_commands.command(name="listresponses", description="List all configured ping responses.")
    @app_commands.check(is_admin_or_role)
    async def list_responses(self, interaction: discord.Interaction):
        config = await data_manager.get_server_config(interaction.guild_id)
        responses = config.get("mention_responses", [])
        if not responses:
            return await interaction.response.send_message("No responses configured.", ephemeral=True)
            
        text = "\n".join([f"{i+1}. {r}" for i, r in enumerate(responses)])
        await interaction.response.send_message(f"**Configured Responses:**\n{text}", ephemeral=True)

    @app_commands.command(name="removeresponse", description="Remove a ping response by index.")
    @app_commands.describe(index="The index of the response to remove (see /listresponses).")
    @app_commands.check(is_admin_or_role)
    async def remove_response(self, interaction: discord.Interaction, index: int):
        config = await data_manager.get_server_config(interaction.guild_id)
        responses = config.get("mention_responses", [])
        
        idx = index - 1
        if 0 <= idx < len(responses):
            removed = responses.pop(idx)
            await data_manager.set_server_config(interaction.guild_id, "mention_responses", responses)
            await interaction.response.send_message(f"Removed response: `{removed}`", ephemeral=True)
        else:
            await interaction.response.send_message("Invalid index.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Admin(bot))
