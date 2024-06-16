import discord
from redbot.core import Config, checks, commands

class StaffManager(commands.Cog):
    """Cog for managing staff members in a Discord server."""

    def __init__(self, bot):
        self.bot = bot
        self.staff_updates_channel = None
        self.blacklist_channel = None

    @commands.group()
    async def staff(self, ctx):
        """Staff management commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid staff command. Use `/staff help` for a list of commands.")

    @staff.command(name="setupdates")
    @commands.has_permissions(manage_channels=True)
    async def staff_setupdates(self, ctx, channel: discord.TextChannel):
        """Set the channel for staff update messages."""
        self.staff_updates_channel = channel
        await ctx.send(f"Staff updates channel set to {channel.mention}")

    @staff.command(name="setblacklist")
    @commands.has_permissions(manage_channels=True)
    async def staff_setblacklist(self, ctx, channel: discord.TextChannel):
        """Set the channel for blacklist messages."""
        self.blacklist_channel = channel
        await ctx.send(f"Blacklist channel set to {channel.mention}")

    @staff.command(name="fire")
    @commands.has_permissions(manage_roles=True)
    async def staff_fire(self, ctx, member: discord.Member, role: discord.Role):
        """Fire a staff member."""
        await member.remove_roles(role)
        embed = discord.Embed(title="Staff Fired", color=discord.Color.red())
        embed.add_field(name="Username", value=member.name, inline=False)
        embed.add_field(name="User ID", value=member.id, inline=False)
        embed.add_field(name="Position", value=role.name, inline=False)
        embed.add_field(name="Issuer", value=ctx.author.name, inline=False)
        await self.staff_updates_channel.send(embed=embed)

    @staff.command(name="hire")
    @commands.has_permissions(manage_roles=True)
    async def staff_hire(self, ctx, member: discord.Member, role: discord.Role):
        """Hire a new staff member."""
        await member.add_roles(role)
        embed = discord.Embed(title="Staff Hired", color=discord.Color.green())
        embed.add_field(name="Username", value=member.name, inline=False)
        embed.add_field(name="User ID", value=member.id, inline=False)
        embed.add_field(name="Position", value=role.name, inline=False)
        embed.add_field(name="Issuer", value=ctx.author.name, inline=False)
        await self.staff_updates_channel.send(embed=embed)

    @staff.command(name="demote")
    @commands.has_permissions(manage_roles=True)
    async def staff_demote(self, ctx, member: discord.Member, old_role: discord.Role, new_role: discord.Role):
        """Demote a staff member."""
        await member.remove_roles(old_role)
        await member.add_roles(new_role)
        embed = discord.Embed(title="Staff Demoted", color=discord.Color.orange())
        embed.add_field(name="Username", value=member.name, inline=False)
        embed.add_field(name="User ID", value=member.id, inline=False)
        embed.add_field(name="Position", value=new_role.name, inline=False)
        embed.add_field(name="Old Position", value=old_role.name, inline=False)
        embed.add_field(name="Issuer", value=ctx.author.name, inline=False)
        await self.staff_updates_channel.send(embed=embed)

    @staff.command(name="promote")
    @commands.has_permissions(manage_roles=True)
    async def staff_promote(self, ctx, member: discord.Member, old_role: discord.Role, new_role: discord.Role):
        """Promote a staff member."""
        await member.remove_roles(old_role)
        await member.add_roles(new_role)
        embed = discord.Embed(title="Staff Promoted", color=discord.Color.blue())
        embed.add_field(name="Username", value=member.name, inline=False)
        embed.add_field(name="User ID", value=member.id, inline=False)
        embed.add_field(name="Position", value=new_role.name, inline=False)
        embed.add_field(name="Old Position", value=old_role.name, inline=False)
        embed.add_field(name="Issuer", value=ctx.author.name, inline=False)
        await self.staff_updates_channel.send(embed=embed)

    @staff.command(name="blacklist")
    @commands.has_permissions(ban_members=True)
    async def staff_blacklist(self, ctx, member: discord.Member, reason: str, proof: str):
        """Blacklist a staff member."""
    try:
        await member.send(f"You have been blacklisted from {ctx.guild.name} for: {reason}. If you wish to appeal, please contact the guild owner or the staff team.")
    except discord.Forbidden:
        await ctx.send(f"Failed to send a DM to {member.name}. They will still be blacklisted.")

        await member.ban(reason=reason)
        embed = discord.Embed(title="Staff Blacklisted", color=discord.Color.dark_red())
        embed.add_field(name="Username", value=member.name, inline=False)
        embed.add_field(name="User ID", value=member.id, inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Proof", value=proof, inline=False)
        embed.add_field(name="Issuer", value=ctx.author.name, inline=False)
        embed.add_field(name="Appeal", value=f"To appeal, contact {ctx.guild.owner.mention}")
        await self.blacklist_channel.send(embed=embed)

def setup(bot):
    bot.add_cog(StaffManager(bot))
