import discord
from redbot.core import commands, Config

class InviteSettings(commands.Cog):
    """Manage invites and their messages."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_global = {
            "admin_invite": None,
            "main_invite": None,
            "support_server": None,
            "admin_message": None,
            "main_message": None,
            "support_message": None,
        }
        self.config.register_global(**default_global)

        # Remove the existing invite command if it exists
        existing_invite = self.bot.get_command("invite")
        if existing_invite:
            self.bot.remove_command(existing_invite.name)

    @commands.group()
    async def invite(self, ctx):
        """Invite management commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @invite.group()
    @commands.is_owner()
    async def set(self, ctx):
        """Set invite links and messages."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @set.command(name="admin")
    async def set_admin_invite(self, ctx, invite: str, *, message: str = None):
        """Set the admin invite link and optional message."""
        await self.config.admin_invite.set(invite)
        await self.config.admin_message.set(message)
        await ctx.send("Admin invite link and message set.")

    @set.command(name="main")
    async def set_main_invite(self, ctx, invite: str, *, message: str = None):
        """Set the main invite link and optional message."""
        await self.config.main_invite.set(invite)
        await self.config.main_message.set(message)
        await ctx.send("Main invite link and message set.")

    @set.command(name="support")
    async def set_support_server(self, ctx, invite: str, *, message: str = None):
        """Set the support server invite link and optional message."""
        await self.config.support_server.set(invite)
        await self.config.support_message.set(message)
        await ctx.send("Support server invite link and message set.")

    @invite.command(name="show")
    async def show_invites(self, ctx):
        """Show all set invites and their messages."""
        admin_invite = await self.config.admin_invite()
        main_invite = await self.config.main_invite()
        support_server = await self.config.support_server()
        admin_message = await self.config.admin_message()
        main_message = await self.config.main_message()
        support_message = await self.config.support_message()

        embed = discord.Embed(title="Invite Links and Messages")
        embed.add_field(name="Admin Message", value=admin_message or "Not set", inline=False)
        embed.add_field(name="Admin Invite", value=admin_invite or "Not set", inline=False)
        embed.add_field(name="Main Message", value=main_message or "Not set", inline=False)
        embed.add_field(name="Main Invite", value=main_invite or "Not set", inline=False)
        embed.add_field(name="Support Message", value=support_message or "Not set", inline=False)
        embed.add_field(name="Support Server", value=support_server or "Not set", inline=False)

        await ctx.send(embed=embed)
