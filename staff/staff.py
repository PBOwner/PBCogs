import discord
from redbot.core import Config, checks, commands
class StaffManager(commands.Cog):
    """Cog for managing staff members in a Discord server."""
    def __init__(self, bot):
        self.bot = bot
        self.staff_updates_channel = None
        self.blacklist_channel = None
        self.config = Config.get_conf(self, identifier="staffmanager", force_registration=True)
        self.config.register_global(staff_updates_channel=None, blacklist_channel=None)
        
    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def setupdates(self, ctx, channel: discord.TextChannel):
        """Set the channel for staff update messages."""
        self.staff_updates_channel = channel
        await ctx.send(f"Staff updates channel set to {channel.mention}")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def setblacklist(self, ctx, channel: discord.TextChannel):
        """Set the channel for blacklist messages."""
        await self.config.blacklist_channel.set(channel)
        await ctx.send(f"Blacklist channel set to {channel.mention}")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Handle command errors."""
        if isinstance(error, commands.CheckFailure):
            await self.send_channel_not_set_message(ctx, ctx.command.name)

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
    async def demote(self, ctx, member: discord.Member, old_role: discord.Role, new_role: discord.Role):
        """Demote a staff member."""
        await member.remove_roles(old_role)
        await member.add_roles(new_role)
        embed = discord.Embed(title="Staff Demoted", color=discord.Color.orange())
        embed.add_field(name="Username", value=member.name, inline=False)
        embed.add_field(name="User ID", value=member.id, inline=False)
        embed.add_field(name="Position", value=new_role.name, inline=False)
        embed.add_field(name="Old Position", value=old_role.name, inline=False)
        channel = await self.config.staff_updates_channel()

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
        channel = await self.config.staff_updates_channel()
        if channel:
            await channel.send(embed=embed)
        else:
            await self.send_channel_reminder(ctx, "promote")

    @commands.command(name="staffblacklist")
    @commands.has_permissions(ban_members=True)
    async def staffblacklist(self, ctx, member: discord.Member, reason: str, proof: str):
        """Blacklist a staff member."""
        # Send a DM to the member before banning them
        try:
            await member.send(f"You have been blacklisted from {ctx.guild.name} for: {reason}. If you wish to appeal, please contact {ctx.guild.owner.mention} or the Support team.")
        except discord.Forbidden:
            await ctx.send(f"Failed to send a DM to {member.name}. They will still be blacklisted.")
        # Ban the member
        await member.ban(reason=reason)
        # Send an embed message to the blacklist_channel
        embed = discord.Embed(title="Staff Blacklisted", color=discord.Color.dark_red())
        embed.add_field(name="Username", value=member.name, inline=False)
        embed.add_field(name="User ID", value=member.id, inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Proof", value=proof, inline=False)
        channel = await self.config.blacklist_channel()
        if channel:
            await channel.send(embed=embed)
        else:
            await self.send_channel_reminder(ctx, "staffblacklist")

def setup(bot):
    bot.add_cog(StaffManager(bot))
