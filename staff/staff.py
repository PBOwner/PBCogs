import discord
from redbot.core import commands, Config, checks

class StaffManager(commands.Cog):
    """Cog for managing staff members in a Discord server"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=123456789)
        self.config.register_guild(
            blacklist_channel=None,
            blacklist_proof=None
        )

    @commands.command()
    @checks.admin_or_permissions(manage_roles=True)
    async def fire(self, ctx, member: discord.Member):
        """
        Removes a member from the staff team.

        Parameters:
        member (discord.Member): The member to be fired.
        """
        # Remove the member's staff role
        await member.remove_roles(discord.utils.get(ctx.guild.roles, name="Staff"))
        await ctx.send(f"{member.mention} has been fired from the staff team.")

    @commands.command()
    @checks.admin_or_permissions(manage_roles=True)
    async def hire(self, ctx, member: discord.Member):
        """
        Adds a member to the staff team.

        Parameters:
        member (discord.Member): The member to be hired.
        """
        # Add the staff role to the member
        await member.add_roles(discord.utils.get(ctx.guild.roles, name="Staff"))
        await ctx.send(f"{member.mention} has been hired as a staff member.")

    @commands.command()
    @checks.admin_or_permissions(manage_roles=True)
    async def demote(self, ctx, member: discord.Member):
        """
        Demotes a staff member to a regular member.

        Parameters:
        member (discord.Member): The staff member to be demoted.
        """
        # Remove the staff role from the member
        await member.remove_roles(discord.utils.get(ctx.guild.roles, name="Staff"))
        await ctx.send(f"{member.mention} has been demoted from the staff team.")

    @commands.command()
    @checks.admin_or_permissions(manage_roles=True)
    async def promote(self, ctx, member: discord.Member):
        """
        Promotes a member to the staff team.

        Parameters:
        member (discord.Member): The member to be promoted.
        """
        # Add the staff role to the member
        await member.add_roles(discord.utils.get(ctx.guild.roles, name="Staff"))
        await ctx.send(f"{member.mention} has been promoted to the staff team.")

    @commands.command()
    @checks.admin_or_permissions(manage_roles=True)
    async def blacklist(self, ctx, member: discord.Member, *, reason: str):
        """
        Blacklists a member from the server and sends a message to a configurable channel.

        Parameters:
        member (discord.Member): The member to be blacklisted.
        reason (str): The reason for the blacklisting.
        """
        # Kick the member from the server
        await member.kick(reason=reason)

        # Get the blacklist channel and proof settings
        blacklist_channel = await self.config.guild(ctx.guild).blacklist_channel()
        blacklist_proof = await self.config.guild(ctx.guild).blacklist_proof()

        # Send the blacklist message to the configured channel
        channel = ctx.guild.get_channel(blacklist_channel)
        if channel:
            await channel.send(f"{member.id} was blacklisted from {ctx.guild.name} for {reason} with {blacklist_proof}")
        else:
            await ctx.send(f"{member.id} was blacklisted from {ctx.guild.name} for {reason}")
