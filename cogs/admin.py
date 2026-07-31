import discord
from discord import app_commands
from discord.ext import commands
from core.data_manager import data_manager

async def is_admin_or_role(interaction: discord.Interaction):
    if interaction.user.guild_permissions.administrator:
        return True
    
    config = await data_manager.get_server_config(interaction.guild_id)
    admin_role_ids = config.get("admin_role_ids", [])
    
    old_admin_role_id = config.get("admin_role_id")
    if old_admin_role_id and old_admin_role_id not in admin_role_ids:
        admin_role_ids.append(old_admin_role_id)
        
    for role_id in admin_role_ids:
        role = interaction.guild.get_role(role_id)
        if role and role in interaction.user.roles:
            return True
            
    await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
    return False

async def is_supporter_or_admin(interaction: discord.Interaction):
    if interaction.user.guild_permissions.administrator:
        return True
    
    config = await data_manager.get_server_config(interaction.guild_id)
    admin_role_ids = config.get("admin_role_ids", [])
    
    old_admin_role_id = config.get("admin_role_id")
    if old_admin_role_id and old_admin_role_id not in admin_role_ids:
        admin_role_ids.append(old_admin_role_id)
        
    for role_id in admin_role_ids:
        role = interaction.guild.get_role(role_id)
        if role and role in interaction.user.roles:
            return True
            
    supporter_role_id = config.get("supporter_role_id")
    if supporter_role_id:
        role = interaction.guild.get_role(supporter_role_id)
        if role and role in interaction.user.roles:
            return True
            
    await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
    return False

class RolesConfigView(discord.ui.View):
    def __init__(self, guild: discord.Guild, config):
        super().__init__(timeout=900)
        self.guild = guild
        self.config = config.copy()
        
        # Migrate old configs locally
        old_admin = self.config.get("admin_role_id")
        if old_admin:
            admin_roles = self.config.setdefault("admin_role_ids", [])
            if old_admin not in admin_roles:
                admin_roles.append(old_admin)
                
        old_supporter = self.config.get("supporter_role_id")
        if old_supporter:
            supporter_roles = self.config.setdefault("supporter_role_ids", [])
            if old_supporter not in supporter_roles:
                supporter_roles.append(old_supporter)

        self.update_components()

    def update_components(self):
        self.clear_items()
        
        # Row 0: Add Admin Roles
        admin_add = discord.ui.RoleSelect(
            custom_id="admin_role_add",
            placeholder="Add Admin Roles...",
            min_values=1,
            max_values=25,
            row=0
        )
        admin_add.callback = self.admin_add_callback
        self.add_item(admin_add)

        # Row 1: Add Supporter Roles
        supporter_add = discord.ui.RoleSelect(
            custom_id="supporter_role_add",
            placeholder="Add Supporter Roles...",
            min_values=1,
            max_values=25,
            row=1
        )
        supporter_add.callback = self.supporter_add_callback
        self.add_item(supporter_add)
        
        # Row 2: Remove Admin Roles
        admin_roles = self.config.get("admin_role_ids", [])
        if admin_roles:
            options = []
            for r_id in admin_roles:
                role = self.guild.get_role(r_id)
                name = role.name if role else f"Unknown Role ({r_id})"
                options.append(discord.SelectOption(label=name, value=str(r_id)))
            
            # Max 25 options per select
            if len(options) > 25:
                options = options[:25]
                
            admin_remove = discord.ui.Select(
                custom_id="admin_role_remove",
                placeholder="Remove Admin Roles...",
                min_values=1,
                max_values=len(options),
                options=options,
                row=2
            )
            admin_remove.callback = self.admin_remove_callback
            self.add_item(admin_remove)

        # Row 3: Remove Supporter Roles
        supporter_roles = self.config.get("supporter_role_ids", [])
        if supporter_roles:
            options = []
            for r_id in supporter_roles:
                role = self.guild.get_role(r_id)
                name = role.name if role else f"Unknown Role ({r_id})"
                options.append(discord.SelectOption(label=name, value=str(r_id)))
            
            if len(options) > 25:
                options = options[:25]
                
            supporter_remove = discord.ui.Select(
                custom_id="supporter_role_remove",
                placeholder="Remove Supporter Roles...",
                min_values=1,
                max_values=len(options),
                options=options,
                row=3
            )
            supporter_remove.callback = self.supporter_remove_callback
            self.add_item(supporter_remove)

        # Row 4: Clear Buttons
        if admin_roles or supporter_roles:
            if admin_roles:
                clear_admin = discord.ui.Button(label="Clear Admin Roles", style=discord.ButtonStyle.danger, custom_id="clear_admin_roles", row=4)
                clear_admin.callback = self.clear_admin_callback
                self.add_item(clear_admin)
                
            if supporter_roles:
                clear_supporter = discord.ui.Button(label="Clear Supporter Roles", style=discord.ButtonStyle.danger, custom_id="clear_supporter_roles", row=4)
                clear_supporter.callback = self.clear_supporter_callback
                self.add_item(clear_supporter)

    async def admin_add_callback(self, interaction: discord.Interaction):
        selected = interaction.data.get('values', [])
        admin_roles = self.config.setdefault("admin_role_ids", [])
        for r_id in selected:
            r_id = int(r_id)
            if r_id not in admin_roles:
                admin_roles.append(r_id)
        await self.save_and_update(interaction)

    async def supporter_add_callback(self, interaction: discord.Interaction):
        selected = interaction.data.get('values', [])
        supporter_roles = self.config.setdefault("supporter_role_ids", [])
        for r_id in selected:
            r_id = int(r_id)
            if r_id not in supporter_roles:
                supporter_roles.append(r_id)
        await self.save_and_update(interaction)
        
    async def admin_remove_callback(self, interaction: discord.Interaction):
        selected = [int(v) for v in interaction.data.get('values', [])]
        admin_roles = self.config.get("admin_role_ids", [])
        self.config["admin_role_ids"] = [r for r in admin_roles if r not in selected]
        await self.save_and_update(interaction)

    async def supporter_remove_callback(self, interaction: discord.Interaction):
        selected = [int(v) for v in interaction.data.get('values', [])]
        supporter_roles = self.config.get("supporter_role_ids", [])
        self.config["supporter_role_ids"] = [r for r in supporter_roles if r not in selected]
        await self.save_and_update(interaction)

    async def clear_admin_callback(self, interaction: discord.Interaction):
        self.config["admin_role_ids"] = []
        await self.save_and_update(interaction)

    async def clear_supporter_callback(self, interaction: discord.Interaction):
        self.config["supporter_role_ids"] = []
        await self.save_and_update(interaction)

    async def save_and_update(self, interaction: discord.Interaction):
        self.config.pop("admin_role_id", None)
        self.config.pop("supporter_role_id", None)
        
        await data_manager.set_server_config(self.guild.id, "admin_role_ids", self.config.get("admin_role_ids", []))
        await data_manager.set_server_config(self.guild.id, "supporter_role_ids", self.config.get("supporter_role_ids", []))
        
        self.update_components()
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    def create_embed(self):
        embed = discord.Embed(title="🛡️ Roles Configuration", color=discord.Color.blurple())
        embed.description = "Use the dropdowns below to configure roles for Admin and Supporter permissions."
        
        admin_roles = self.config.get("admin_role_ids", [])
        if admin_roles:
            formatted_admins = [f"<@&{r_id}>" for r_id in admin_roles]
            embed.add_field(name="Admin Roles", value="\n".join(formatted_admins), inline=False)
        else:
            embed.add_field(name="Admin Roles", value="None configured. (Server Administrators are admins by default)", inline=False)

        supporter_roles = self.config.get("supporter_role_ids", [])
        if supporter_roles:
            formatted_supporters = [f"<@&{r_id}>" for r_id in supporter_roles]
            embed.add_field(name="Supporter Roles", value="\n".join(formatted_supporters), inline=False)
        else:
            embed.add_field(name="Supporter Roles", value="None configured.", inline=False)
            
        return embed

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="rolesconfig", description="Open the interactive role configuration dashboard.")
    @app_commands.default_permissions(administrator=True)
    async def rolesconfig(self, interaction: discord.Interaction):
        config = await data_manager.get_server_config(interaction.guild_id)
        view = RolesConfigView(interaction.guild, config)
        embed = view.create_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="setlogchannel", description="Set the channel where bot logs will be sent.")
    @app_commands.describe(channel="The text channel for logs.")
    @app_commands.check(is_admin_or_role)
    async def set_log_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await data_manager.set_server_config(interaction.guild_id, "log_channel_id", channel.id)
        await interaction.response.send_message(f"Log channel set to {channel.mention}.", ephemeral=True)

    @app_commands.command(name="say", description="Send an anonymous message through the bot.")
    @app_commands.describe(
        message="The message to send.",
        message_id="Optional ID of a message to reply to."
    )
    @app_commands.check(is_supporter_or_admin)
    async def say_command(self, interaction: discord.Interaction, message: str, message_id: str = None):
        await interaction.response.send_message("Message sent!", ephemeral=True)
        
        reply_to = None
        if message_id:
            try:
                reply_to = await interaction.channel.fetch_message(int(message_id))
            except (discord.NotFound, discord.HTTPException, ValueError):
                pass
                
        if reply_to:
            await reply_to.reply(message)
        else:
            await interaction.channel.send(message)
        
        config = await data_manager.get_server_config(interaction.guild_id)
        log_channel_id = config.get("log_channel_id")
        if log_channel_id:
            log_channel = interaction.guild.get_channel(log_channel_id)
            if log_channel:
                embed = discord.Embed(title="Anonymous Say Log", color=discord.Color.red())
                embed.add_field(name="User", value=interaction.user.mention, inline=True)
                embed.add_field(name="Channel", value=interaction.channel.mention, inline=True)
                if message_id:
                    embed.add_field(name="Reply To ID", value=message_id, inline=True)
                embed.add_field(name="Message", value=message, inline=False)
                await log_channel.send(embed=embed)

    @app_commands.command(name="addresponse", description="Add a random response when the bot is mentioned.")
    @app_commands.describe(response="The text to add.")
    @app_commands.check(is_supporter_or_admin)
    async def add_response(self, interaction: discord.Interaction, response: str):
        config = await data_manager.get_server_config(interaction.guild_id)
        responses = config.get("mention_responses", [])
        responses.append(response)
        await data_manager.set_server_config(interaction.guild_id, "mention_responses", responses)
        await interaction.response.send_message(f"Added response: `{response}`", ephemeral=True)

    @app_commands.command(name="listresponses", description="List all configured ping responses.")
    @app_commands.check(is_supporter_or_admin)
    async def list_responses(self, interaction: discord.Interaction):
        config = await data_manager.get_server_config(interaction.guild_id)
        responses = config.get("mention_responses", [])
        if not responses:
            return await interaction.response.send_message("No responses configured.", ephemeral=True)
            
        text = "\n".join([f"{i+1}. {r}" for i, r in enumerate(responses)])
        await interaction.response.send_message(f"**Configured Responses:**\n{text}", ephemeral=True)

    @app_commands.command(name="removeresponse", description="Remove a ping response by index.")
    @app_commands.describe(index="The index of the response to remove (see /listresponses).")
    @app_commands.check(is_supporter_or_admin)
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

    @app_commands.command(name="botstats", description="Check how many servers and users the bot is currently in.")
    @app_commands.default_permissions(administrator=True)
    async def get_bot_stats(self, interaction: discord.Interaction):
        # Ensure only the bot owner can view this sensitive information
        if not await self.bot.is_owner(interaction.user):
            return await interaction.response.send_message("Only the bot owner can use this command.", ephemeral=True)
            
        guilds = self.bot.guilds
        total_members = sum(g.member_count for g in guilds if g.member_count is not None)
        
        guild_list = "\n".join([f"- {g.name} ({g.member_count} members)" for g in guilds])
        if len(guild_list) > 1800:
            guild_list = guild_list[:1800] + "\n... (truncated)"
            
        embed = discord.Embed(title="Bot Statistics", color=discord.Color.blue())
        embed.add_field(name="Total Servers", value=str(len(guilds)), inline=True)
        embed.add_field(name="Total Users", value=str(total_members), inline=True)
        embed.description = f"**Servers:**\n{guild_list}"
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Admin(bot))
