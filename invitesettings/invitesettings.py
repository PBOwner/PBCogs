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
            }
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
        """Set invite links and field names."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @set.command(name="invite")
    async def set_invite(self, ctx, invite_type: str, invite: str):
        """Set an invite link.

        **Arguments**
            - `invite_type`: The type of invite (e.g., main, admin, support).
            - `invite`: The invite link.
        """
        async with self.config.invites() as invites:
            if invite_type not in invites:
                return await ctx.send("Invalid invite type. Valid types are: main, admin, support.")
            invites[invite_type]["link"] = invite
        await ctx.send(f"{invite_type.capitalize()} invite link set.")

    @set.command(name="fieldname")
    async def set_field_name(self, ctx, invite_type: str, *, field_name: str):
        """Set the field name for an invite type.

        **Arguments**
            - `invite_type`: The type of invite (e.g., main, admin, support).
            - `field_name`: The field name to display in the embed.
        """
        async with self.config.invites() as invites:
            if invite_type not in invites:
                return await ctx.send("Invalid invite type. Valid types are: main, admin, support.")
            invites[invite_type]["field_name"] = field_name
        await ctx.send(f"Field name for {invite_type.capitalize()} invite set to {field_name}.")

    @invite.command(name="show")
    async def show_invites(self, ctx):
        """Show all set invites."""
        invites = await self.config.invites()
        embed = discord.Embed(title="Invite Links")

        for key, value in invites.items():
            field_name = value.get("field_name", key.capitalize())
            link = value.get("link", "Not set")
            embed.add_field(name=field_name, value=link, inline=False)

        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(InviteSettings(bot))
