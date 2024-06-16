import discord
from redbot.core import Config, checks, commands

class StaffManager(commands.Cog):
    """Cog for managing staff members in a Discord server."""

    def __init__(self, bot):
        self.bot = bot
        self.staff_updates_channel = None
        self.blacklist_channel = None

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def setstaffupdates(self, ctx, channel: discord.TextChannel):
        """Set the channel for staff update messages."""
        self.staff_updates_channel = channel
        await ctx.send(f"Staff updates channel set to {channel.mention}")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def setblacklistchannel(self, ctx, channel: discord.TextChannel):
        """Set the channel for blacklist messages."""
        self.blacklist_channel = channel
        await ctx.send(f"Blacklist channel set to {channel.mention}")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def fire(self, ctx, member: discord.Member, role: discord.Role):
        """Fire a staff member."""
        await member.remove_roles(role)
        embed = discord.Embed(title="Staff Fired", color=discord.Color.red())
        embed.add_field(name="Username", value=member.name, inline=False)
        embed.add_field(name="User ID", value=member.id, inline=False)
        embed.add_field(name="Position", value=role.name, inline=False)
        embed.add_field(name="Issuer", value=ctx.author.name, inline=False)
        await self.staff_updates_channel.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def hire(self, ctx, member: discord.Member, role: discord.Role):
        """Hire a new staff member."""
        await member.add_roles(role)
        embed = discord.Embed(title="Staff Hired", color=discord.Color.green())
        embed.add_field(name="Username", value=member.name, inline=False)
        embed.add_field(name="User ID", value=member.id, inline=False)
        embed.add_field(name="Position", value=role.name, inline=False)
        embed.add_field(name="Issuer", value=ctx.author.name, inline=False)
        await self.staff_updates_channel.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def demote(self, ctx, member: discord.Member, old_role: discord.Role, new_role: discord.Role):
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

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def promote(self, ctx, member: discord.Member, old_role: discord.Role, new_role: discord.Role):
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

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def staffblacklist(self, ctx, member: discord.Member, reason: str, proof: str):
        """Blacklist a staff member."""
        await member.ban(reason=reason)
        embed = discord.Embed(title="Staff Blacklisted", color=discord.Color.dark_red())
        embed.add_field(name="Username", value=member.name, inline=False)
        embed.add_field(name="User ID", value=member.id, inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Proof", value=proof, inline=False)
        embed.add_field(name="Issuer", value=ctx.author.name, inline=False)
        embed.add_field(name="Appeal", value=f"To appeal, contact {ctx.guild.owner.mention}")
        await self.blacklist_channel.send(embed=embed)

    @commands.group()
    async def staff(self, ctx):
        """Staff management commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid staff command. Use `/staff help` for a list of commands.")

    @staff.command(name="setstaffupdates")
    @commands.has_permissions(manage_channels=True)
    async def staff_setstaffupdates(self, ctx, channel: discord.TextChannel):
        """Set the channel for staff update messages."""
        self.staff_updates_channel = channel
        await ctx.send(f"Staff updates channel set to {channel.mention}")

    @staff.command(name="setblacklistchannel")
    @commands.has_permissions(manage_channels=True)
    async def staff_setblacklistchannel(self, ctx, channel: discord.TextChannel):
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
