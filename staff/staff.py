import discord
from redbot.core import Config, checks, commands

class StaffManager(commands.Cog):
    """Cog for managing staff members in a Discord server."""
    def __init__(self, bot):
        self.bot = bot
        self.staff_updates_channel = None
        self.blacklist_channel = None
        self.loa_requests_channel = None
        self.loa_role = None
        self.resignation_requests_channel = None
        self.config = Config.get_conf(self, identifier="staffmanager", force_registration=True)
        self.config.register_global(staff_updates_channel=None, blacklist_channel=None, loa_requests_channel=None, loa_role=None, resignation_requests_channel=None, loa_requests={}, resignation_requests={})

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def setupdates(self, ctx, channel: discord.TextChannel):
        """Set the channel for staff update messages."""
        self.staff_updates_channel = channel
        await self.config.staff_updates_channel.set(channel.id)
        await ctx.send(f"Staff updates channel set to {channel.mention}")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def setblacklist(self, ctx, channel: discord.TextChannel):
        """Set the channel for blacklist messages."""
        await self.config.blacklist_channel.set(channel.id)
        await ctx.send(f"Blacklist channel set to {channel.mention}")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Handle command errors."""
        if isinstance(error, commands.CheckFailure):
            await self.send_channel_not_set_message(ctx, ctx.command.name)

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

    @commands.group()
    @commands.has_permissions(manage_roles=True)
    async def loa(self, ctx):
        """Group command for managing leave of absence requests."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid subcommand passed. Use `loa request`, `loa approve`, `loa deny`, `loa channel`, or `loa role`.")

    @loa.command()
    @commands.has_permissions(manage_channels=True)
    async def channel(self, ctx, channel: discord.TextChannel):
        """Set the channel for LOA request messages."""
        self.loa_requests_channel = channel
        await self.config.loa_requests_channel.set(channel.id)
        await ctx.send(f"LOA requests channel set to {channel.mention}")

    @loa.command()
    @commands.has_permissions(manage_roles=True)
    async def role(self, ctx, role: discord.Role):
        """Set the role to be assigned during LOA."""
        self.loa_role = role
        await self.config.loa_role.set(role.id)
        await ctx.send(f"LOA role set to {role.name}")

    @loa.command()
    async def request(self, ctx, duration: str, reason: str):
        """Request a leave of absence."""
        loa_requests = await self.config.loa_requests()
        user_id = ctx.author.id
        loa_requests[user_id] = {
            "user": ctx.author.id,
            "duration": duration,
            "reason": reason,
            "approved_by": None
        }
        await self.config.loa_requests.set(loa_requests)

        loa_requests_channel_id = await self.config.loa_requests_channel()
        loa_requests_channel = self.bot.get_channel(loa_requests_channel_id)
        if loa_requests_channel:
            embed = discord.Embed(title="LOA Request", color=discord.Color.yellow())
            embed.add_field(name="User", value=ctx.author.name, inline=False)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Duration", value=duration, inline=False)
            embed.add_field(name="User ID", value=ctx.author.id, inline=False)
            embed.set_footer(text="Do `loa approve <user_id>` or `loa deny <user_id>`")
            await loa_requests_channel.send(embed=embed)

        await ctx.send(f"Leave of Absence request submitted for {duration} due to {reason}.")

    @loa.command()
    async def approve(self, ctx, user_id: int):
        """Approve a leave of absence request."""
        loa_requests = await self.config.loa_requests()
        if user_id in loa_requests and loa_requests[user_id]["approved_by"] is None:
            loa_requests[user_id]["approved_by"] = ctx.author.id
            await self.config.loa_requests.set(loa_requests)
            user = self.bot.get_user(loa_requests[user_id]["user"])
            loa_role_id = await self.config.loa_role()
            loa_role = ctx.guild.get_role(loa_role_id)
            if loa_role:
                await user.add_roles(loa_role)
            embed = discord.Embed(title="Leave of Absence", color=discord.Color.green())
            embed.add_field(name="User", value=user.name, inline=False)
            embed.add_field(name="Duration", value=loa_requests[user_id]["duration"], inline=False)
            embed.add_field(name="Reason", value=loa_requests[user_id]["reason"], inline=False)
            embed.add_field(name="Approved by", value=ctx.author.name, inline=False)
            await self.staff_updates_channel.send(embed=embed)
            await ctx.send(f"Leave of Absence request for {user.name} approved.")
        else:
            await ctx.send(f"Leave of Absence request for user ID {user_id} not found or already approved.")

    @loa.command()
    async def deny(self, ctx, user_id: int):
        """Deny a leave of absence request."""
        loa_requests = await self.config.loa_requests()
        if user_id in loa_requests:
            del loa_requests[user_id]
            await self.config.loa_requests.set(loa_requests)
            await ctx.send(f"Leave of Absence request for user ID {user_id} denied and removed.")
        else:
            await ctx.send(f"Leave of Absence request for user ID {user_id} not found.")

    @loa.command()
    async def end(self, ctx, user_id: int):
        """End a leave of absence."""
        loa_requests = await self.config.loa_requests()
        if user_id in loa_requests and loa_requests[user_id]["approved_by"] is not None:
            user = self.bot.get_user(loa_requests[user_id]["user"])
            loa_role_id = await self.config.loa_role()
            loa_role = ctx.guild.get_role(loa_role_id)
            if loa_role:
                await user.remove_roles(loa_role)
            del loa_requests[user_id]
            await self.config.loa_requests.set(loa_requests)
            embed = discord.Embed(title="Leave of Absence Ended", color=discord.Color.red())
            embed.add_field(name="User", value=user.name, inline=False)
            embed.add_field(name="User ID", value=user.id, inline=False)
            await self.staff_updates_channel.send(embed=embed)
            await ctx.send(f"Leave of Absence for {user.name} has ended.")
        else:
            await ctx.send(f"Leave of Absence for user ID {user_id} not found or not approved.")

    @commands.group()
    @commands.has_permissions(manage_roles=True)
    async def resign(self, ctx):
        """Group command for managing resignation requests."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid subcommand passed. Use `resign request`, `resign accept`, `resign deny`, or `resign channel`.")

    @resign.command()
    async def request(self, ctx, reason: str):
        """Request a resignation."""
        resignation_requests = await self.config.resignation_requests()
        user_id = ctx.author.id
        resignation_requests[user_id] = {
            "user": ctx.author.id,
            "reason": reason,
            "approved_by": None
        }
        await self.config.resignation_requests.set(resignation_requests)

        resignation_requests_channel_id = await self.config.resignation_requests_channel()
        resignation_requests_channel = self.bot.get_channel(resignation_requests_channel_id)
        if resignation_requests_channel:
            embed = discord.Embed(title="Resignation Request", color=discord.Color.yellow())
            embed.add_field(name="User", value=ctx.author.name, inline=False)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="User ID", value=ctx.author.id, inline=False)
            embed.set_footer(text="Do `resign accept <user_id>` or `resign deny <user_id>`")
            await resignation_requests_channel.send(embed=embed)

        await ctx.send(f"Resignation request submitted due to {reason}.")

    @resign.command()
    async def accept(self, ctx, user_id: int):
        """Accept a resignation request."""
        resignation_requests = await self.config.resignation_requests()
        if user_id in resignation_requests and resignation_requests[user_id]["approved_by"] is None:
            resignation_requests[user_id]["approved_by"] = ctx.author.id
            await self.config.resignation_requests.set(resignation_requests)
            user = self.bot.get_user(resignation_requests[user_id]["user"])
            embed = discord.Embed(title="Staff Member Resigned", color=discord.Color.red())
            embed.add_field(name="Former Staff", value=user.name, inline=False)
            embed.add_field(name="Reason", value=resignation_requests[user_id]["reason"], inline=False)
            embed.add_field(name="Approved by", value=ctx.author.name, inline=False)
            staff_updates_channel_id = await self.config.staff_updates_channel()
            staff_updates_channel = self.bot.get_channel(staff_updates_channel_id)
            if staff_updates_channel:
                await staff_updates_channel.send(embed=embed)
            await ctx.send(f"Resignation request for {user.name} accepted.")
        else:
            await ctx.send(f"Resignation request for user ID {user_id} not found or already accepted.")

    @resign.command()
    async def deny(self, ctx, user_id: int):
        """Deny a resignation request."""
        resignation_requests = await self.config.resignation_requests()
        if user_id in resignation_requests:
            del resignation_requests[user_id]
            await self.config.resignation_requests.set(resignation_requests)
            await ctx.send(f"Resignation request for user ID {user_id} denied and removed.")
        else:
            await ctx.send(f"Resignation request for user ID {user_id} not found.")

    @resign.command()
    @commands.has_permissions(manage_channels=True)
    async def channel(self, ctx, channel: discord.TextChannel):
        """Set the channel for resignation request messages."""
        self.resignation_requests_channel = channel
        await self.config.resignation_requests_channel.set(channel.id)
        await ctx.send(f"Resignation requests channel set to {channel.mention}")

def setup(bot):
    bot.add_cog(StaffManager(bot))
