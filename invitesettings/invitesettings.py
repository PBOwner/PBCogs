import discord
from redbot.core import commands, Config

class InviteSettings(commands.Cog):
    """Manage invites."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_global = {
            "invites": {
                "main": {"link": None, "field_name": "Main"},
                "admin": {"link": None, "field_name": "Admin"},
                "support": {"link": None, "field_name": "Support Server"}
            },
            "embed_color": None,
        }
        self.config.register_global(**default_global)

        # Remove the existing invite command if it exists
        existing_invite = self.bot.get_command("invite")
        if existing_invite:
            self.bot.remove_command(existing_invite.name)

    @commands.group(invoke_without_command=True)
    async def invite(self, ctx):
        """Invite management commands."""
        if ctx.invoked_subcommand is None:
            await self.show_invites(ctx)

    @invite.group(invoke_without_command=True)
    @commands.is_owner()
    async def set(self, ctx):
        """Set invite links, field names, and embed color."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @set.command(name="invite")
    async def set_invite(self, ctx, invite_type: str, name: str, invite_link: str):
        """Set an invite link.

        **Arguments**
            - `invite_type`: The type of invite (e.g., main, admin, support).
            - `name`: The display name for the invite.
            - `invite_link`: The invite link.
        """
        invite_type = invite_type.lower()

        async with self.config.invites() as invites:
            if invite_type not in invites:
                return await ctx.send("Invalid invite type. Valid types are: main, admin, support.")
            invites[invite_type]["link"] = invite_link
            invites[invite_type]["field_name"] = name

        await ctx.send(f"{name} invite link set.")

    @set.command(name="color")
    async def set_color(self, ctx, color: discord.Color):
        """Set the embed color.

        **Arguments**
            - `color`: The color for the embed.
        """
        await self.config.embed_color.set(color.value)
        await ctx.send("Embed color set.")

    @invite.command(name="show")
    async def show_invites(self, ctx):
        """Show all set invites."""
        invites = await self.config.invites()
        embed_color = await self.config.embed_color()

        embed = discord.Embed(title="Invite Links", color=embed_color or discord.Color.default())
        embed.set_thumbnail(url=self.bot.user.avatar.url)

        view = discord.ui.View()

        for key, value in invites.items():
            field_name = value.get("field_name", key.capitalize())
            link = value.get("link", "Not set")
            embed.add_field(name=field_name, value=f"[{field_name}]({link})", inline=False)
            if link != "Not set":
                view.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label=field_name, url=link))

        await ctx.send(embed=embed, view=view)

def setup(bot):
    bot.add_cog(InviteSettings(bot))
