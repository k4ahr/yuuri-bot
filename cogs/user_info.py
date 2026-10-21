import discord
from discord import app_commands
from discord.ext import commands
import typing

def get_asset_links(asset: discord.Asset) -> str:
    """Returns markdown links to download the asset in different formats at 4096px resolution."""
    if "embed/avatars" in asset.url:
        return f"[PNG]({asset.replace(size=4096).url})"
    
    formats = [
        f"[PNG]({asset.replace(size=4096, format='png').url})",
        f"[JPG]({asset.replace(size=4096, format='jpeg').url})",
        f"[WEBP]({asset.replace(size=4096, format='webp').url})"
    ]
    if asset.is_animated():
        formats.append(f"[GIF]({asset.replace(size=4096, format='gif').url})")
    return " • ".join(formats)

class AvatarView(discord.ui.View):
    def __init__(self, user: typing.Union[discord.Member, discord.User], author: typing.Union[discord.Member, discord.User]):
        super().__init__(timeout=180)
        self.user = user
        self.author = author
        self.showing_server = True
        self.message = None
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        
        server_btn = discord.ui.Button(
            label="Server Avatar",
            style=discord.ButtonStyle.primary if self.showing_server else discord.ButtonStyle.secondary,
            custom_id="btn_server_avatar"
        )
        server_btn.callback = self.show_server
        self.add_item(server_btn)

        global_btn = discord.ui.Button(
            label="Global Avatar",
            style=discord.ButtonStyle.primary if not self.showing_server else discord.ButtonStyle.secondary,
            custom_id="btn_global_avatar"
        )
        global_btn.callback = self.show_global
        self.add_item(global_btn)

    def create_embed(self) -> discord.Embed:
        if self.showing_server and isinstance(self.user, discord.Member) and self.user.guild_avatar:
            asset = self.user.guild_avatar
            title = f"{self.user.display_name}'s Server Avatar"
            note = "*Showing server-specific avatar.*"
        else:
            asset = self.user.avatar or self.user.default_avatar
            title = f"{self.user.name}'s Global Avatar"
            note = "*Showing global avatar.*"

        embed = discord.Embed(
            title=title,
            description=f"**Download (4096px):** {get_asset_links(asset)}\n\n{note}",
            color=self.user.color if isinstance(self.user, discord.Member) and self.user.color != discord.Color.default() else discord.Color.blurple()
        )
        embed.set_image(url=asset.replace(size=4096, static_format="png").url)
        embed.set_footer(text=f"Requested by {self.author.display_name} • ID: {self.user.id}")
        return embed

    async def show_server(self, interaction: discord.Interaction):
        self.showing_server = True
        self.update_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    async def show_global(self, interaction: discord.Interaction):
        self.showing_server = False
        self.update_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            if self.message:
                await self.message.edit(view=self)
        except Exception:
            pass

class BannerView(discord.ui.View):
    def __init__(
        self,
        user: typing.Union[discord.Member, discord.User],
        full_user: discord.User,
        author: typing.Union[discord.Member, discord.User]
    ):
        super().__init__(timeout=180)
        self.user = user
        self.full_user = full_user
        self.author = author
        self.showing_server = True
        self.message = None
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        
        server_btn = discord.ui.Button(
            label="Server Banner",
            style=discord.ButtonStyle.primary if self.showing_server else discord.ButtonStyle.secondary,
            custom_id="btn_server_banner"
        )
        server_btn.callback = self.show_server
        self.add_item(server_btn)

        global_btn = discord.ui.Button(
            label="Global Banner",
            style=discord.ButtonStyle.primary if not self.showing_server else discord.ButtonStyle.secondary,
            custom_id="btn_global_banner"
        )
        global_btn.callback = self.show_global
        self.add_item(global_btn)

    def create_embed(self) -> discord.Embed:
        if self.showing_server and isinstance(self.user, discord.Member) and getattr(self.user, 'guild_banner', None):
            asset = self.user.guild_banner
            title = f"{self.user.display_name}'s Server Banner"
            note = "*Showing server-specific banner.*"
        else:
            asset = self.full_user.banner
            title = f"{self.full_user.name}'s Global Banner"
            note = "*Showing global banner.*"

        color = self.full_user.accent_color or (self.user.color if isinstance(self.user, discord.Member) and self.user.color != discord.Color.default() else discord.Color.blurple())

        embed = discord.Embed(
            title=title,
            description=f"**Download (4096px):** {get_asset_links(asset)}\n\n{note}",
            color=color
        )
        embed.set_image(url=asset.replace(size=4096, static_format="png").url)
        embed.set_footer(text=f"Requested by {self.author.display_name} • ID: {self.user.id}")
        return embed

    async def show_server(self, interaction: discord.Interaction):
        self.showing_server = True
        self.update_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    async def show_global(self, interaction: discord.Interaction):
        self.showing_server = False
        self.update_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            if self.message:
                await self.message.edit(view=self)
        except Exception:
            pass

class UserInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="avatar",
        aliases=["av"],
        description="Get the avatar of yourself or another user at the highest quality."
    )
    @app_commands.describe(user="The user to get the avatar of (defaults to yourself)")
    async def avatar(
        self,
        ctx: commands.Context,
        *,
        user: typing.Optional[typing.Union[discord.Member, discord.User]] = None
    ):
        await ctx.defer()
        target = user or ctx.author

        # Check if member has both a server avatar and global avatar
        has_server_avatar = isinstance(target, discord.Member) and target.guild_avatar is not None
        has_global_avatar = target.avatar is not None

        if has_server_avatar and has_global_avatar:
            view = AvatarView(target, ctx.author)
            embed = view.create_embed()
            view.message = await ctx.send(embed=embed, view=view)
        else:
            asset = target.display_avatar
            color = target.color if isinstance(target, discord.Member) and target.color != discord.Color.default() else discord.Color.blurple()
            embed = discord.Embed(
                title=f"{target.display_name}'s Avatar",
                description=f"**Download (4096px):** {get_asset_links(asset)}",
                color=color
            )
            embed.set_image(url=asset.replace(size=4096, static_format="png").url)
            embed.set_footer(text=f"Requested by {ctx.author.display_name} • ID: {target.id}")
            await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="banner",
        aliases=["bn"],
        description="Get the banner of yourself or another user at the highest quality."
    )
    @app_commands.describe(user="The user to get the banner of (defaults to yourself)")
    async def banner(
        self,
        ctx: commands.Context,
        *,
        user: typing.Optional[typing.Union[discord.Member, discord.User]] = None
    ):
        await ctx.defer()
        target = user or ctx.author

        try:
            full_user = await self.bot.fetch_user(target.id)
        except Exception:
            full_user = target

        guild_banner = getattr(target, 'guild_banner', None) if isinstance(target, discord.Member) else None
        global_banner = getattr(full_user, 'banner', None)

        if guild_banner and global_banner:
            view = BannerView(target, full_user, ctx.author)
            embed = view.create_embed()
            view.message = await ctx.send(embed=embed, view=view)
        elif guild_banner or global_banner:
            asset = guild_banner or global_banner
            color = getattr(full_user, 'accent_color', None) or (target.color if isinstance(target, discord.Member) and target.color != discord.Color.default() else discord.Color.blurple())
            embed = discord.Embed(
                title=f"{target.display_name}'s Banner",
                description=f"**Download (4096px):** {get_asset_links(asset)}",
                color=color
            )
            embed.set_image(url=asset.replace(size=4096, static_format="png").url)
            embed.set_footer(text=f"Requested by {ctx.author.display_name} • ID: {target.id}")
            await ctx.send(embed=embed)
        else:
            accent_color = getattr(full_user, 'accent_color', None)
            if accent_color:
                hex_color = f"#{accent_color.value:06X}"
                embed = discord.Embed(
                    title=f"{target.display_name}'s Banner",
                    description=f"ℹ️ {target.mention} does not have a custom banner image, but has a profile accent color: **{hex_color}**",
                    color=accent_color
                )
            else:
                embed = discord.Embed(
                    title=f"{target.display_name}'s Banner",
                    description=f"ℹ️ {target.mention} does not have a custom banner or accent color set.",
                    color=discord.Color.blurple()
                )
            embed.set_footer(text=f"Requested by {ctx.author.display_name} • ID: {target.id}")
            await ctx.send(embed=embed)

    @avatar.error
    async def avatar_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, (commands.UserNotFound, commands.MemberNotFound, commands.BadUnionArgument)):
            await ctx.send("❌ Could not find that user. Please mention a user, provide a valid User ID, or their username.", ephemeral=True)
        else:
            await ctx.send(f"❌ An error occurred: {error}", ephemeral=True)

    @banner.error
    async def banner_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, (commands.UserNotFound, commands.MemberNotFound, commands.BadUnionArgument)):
            await ctx.send("❌ Could not find that user. Please mention a user, provide a valid User ID, or their username.", ephemeral=True)
        else:
            await ctx.send(f"❌ An error occurred: {error}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(UserInfo(bot))
