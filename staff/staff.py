"""
Staff Manager Cog for Red-DiscordBot
"""

import discord
from redbot.core import commands, Config, checks

class StaffManager(commands.Cog):
    """
    Cog for managing staff members in a Discord server.
    """

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=123456789)
        self.config.register_guild(
            blacklist_channel=None
        )

    @commands.command()
    @checks.admin_or_permissions(manage_roles=True)
    async def fire(self, ctx, member: discord.Member, *, reason: str):
        """
        Removes a member from the staff team.
        """
        # Remove the member's staff role
        await member.remove_roles(discord.utils.get(ctx.guild.roles, name="Staff"))
        await ctx.send(f"{member.mention} has been fired from the staff team for: {reason}")

    @commands.command()
    @checks.admin_or_permissions(manage_roles=True)
    async def hire(self, ctx, member: discord.Member):
        """
        Adds a member to the staff team.
        """
        # Give the member the staff role
        await member.add_roles(discord.utils.get(ctx.guild.roles, name="Staff"))
        await ctx.send(f"{member.mention} has been hired as a new staff member!")

    @commands.command()
    @checks.admin_or_permissions(manage_roles=True)
    async def demote(self, ctx, member: discord.Member, *, reason: str):
        """
        Demotes a staff member.
        """
        # Remove the member's staff role
        await member.remove_roles(discord.utils.get(ctx.guild.roles, name="Staff"))
        await ctx.send(f"{member.mention} has been demoted from the staff team for: {reason}")

    @commands.command()
    @checks.admin_or_permissions(manage_roles=True)
    async def promote(self, ctx, member: discord.Member):
        """
        Promotes a member to the staff team.
        """
        # Give the member the staff role
        await member.add_roles(discord.utils.get(ctx.guild.roles, name="Staff"))
        await ctx.send(f"{member.mention} has been promoted to the staff team!")

    @commands.command()
    @checks.admin_or_permissions(manage_roles=True)
    async def staffblacklist(self, ctx, member: discord.Member, *, reason: str):
        """
        Blacklists a member from the server and sends a message to a configurable channel.
        """
        # Kick the member from the server
        await member.kick(reason=reason)

        # Get the blacklist channel
        blacklist_channel = await self.config.guild(ctx.guild).blacklist_channel()
        if blacklist_channel:
            channel = ctx.guild.get_channel(blacklist_channel)
            await channel.send(f"{member.id} was blacklisted from {ctx.guild.name} for {reason}")
        else:
            await ctx.send(f"{member.id} was blacklisted from {ctx.guild.name} for {reason}")

def setup(bot):
    """
    Loads the StaffManager cog.
    """
    bot.add_cog(StaffManager(bot))
