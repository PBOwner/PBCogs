import discord
from discord.ext import commands, tasks
import asyncio
from redbot.core import Config

class StaffApps(commands.Cog):
    """Cog for handling staff applications and managing staff members."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "application_channel": None,
            "questions": {},
            "applications": {},
            "staff_updates_channel": None,
            "blacklist_channel": None,
            "loa_requests_channel": None,
            "loa_role": None,
            "resignation_requests_channel": None,
            "loa_requests": {},
            "resignation_requests": {}
        }
        self.config.register_guild(**default_guild)

    @commands.guild_only()
    @commands.command()
    async def addq(self, ctx, role: discord.Role, *, question: str):
        """Add a question for a specific role."""
        async with self.config.guild(ctx.guild).questions() as questions:
            questions.setdefault(str(role.id), []).append(question)
        await ctx.send(f"Question added for {role.name}.")

    @commands.guild_only()
    @commands.command()
    async def setappchannel(self, ctx, channel: discord.TextChannel):
        """Set the application channel."""
        await self.config.guild(ctx.guild).application_channel.set(channel.id)
        await ctx.send(f"Application channel set to {channel.mention}.")

    @commands.guild_only()
    @commands.command()
    async def listroles(self, ctx):
        """List roles available for application."""
        questions = await self.config.guild(ctx.guild).questions()
        roles = [ctx.guild.get_role(int(role_id)).name for role_id in questions if ctx.guild.get_role(int(role_id))]
        if roles:
            roles_list = '\n'.join(roles)
            await ctx.send("Roles available for application:\n{}\n\nUse `apply <role_name>` to apply for a role.".format(roles_list))
        else:
            await ctx.send("No roles set for applications.")

    @commands.guild_only()
    @commands.command()
    async def apply(self, ctx, *, role_name: str):
        """Apply for a specific role."""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            return await ctx.send("Role not found.")

        questions = await self.config.guild(ctx.guild).questions()
        role_questions = questions.get(str(role.id))
        if not role_questions:
            return await ctx.send("No questions set for this role.")

        responses = {}
        for question in role_questions:
            await ctx.author.send(f"Question: {question}\nPlease respond in this DM.")
            try:
                response = await self.bot.wait_for(
                    "message",
                    check=lambda m: m.author == ctx.author and m.channel.type == discord.ChannelType.private,
                    timeout=300
                )
                responses[question] = response.content
            except asyncio.TimeoutError:
                await ctx.author.send("Time's up. Please try again later.")
                return

        async with self.config.guild(ctx.guild).applications() as applications:
            applications.setdefault(str(role.id), {}).setdefault(str(ctx.author.id), responses)

        application_channel_id = await self.config.guild(ctx.guild).application_channel()
        application_channel = self.bot.get_channel(application_channel_id)

        if application_channel:
            embed = discord.Embed(title=f"New Application for {role.name} - {ctx.author.display_name} - {ctx.author.id}", color=discord.Color.blue())
            for question, response in responses.items():
                embed.add_field(name=f"Question: {question}", value=f"Response: {response}", inline=False)
            message = await application_channel.send(embed=embed)
            poll_message = await application_channel.send("Should we hire them?")
            await poll_message.add_reaction("✅")
            await poll_message.add_reaction("❌")
            self.bot.loop.create_task(self.tally_votes(poll_message, ctx.channel))
            await ctx.send("Application submitted. Thank you!")
        else:
            await ctx.send("Application channel not set. Please set an application channel using the `setappchannel` command.")

    async def tally_votes(self, poll_message, channel):
        await asyncio.sleep(14400)  # 4 hours in seconds
        poll_message = await poll_message.channel.fetch_message(poll_message.id)
        yes_votes = sum(1 for reaction in poll_message.reactions if reaction.emoji == "✅")
        no_votes = sum(1 for reaction in poll_message.reactions if reaction.emoji == "❌")
        await channel.send(f"Voting has ended. Results:\nYes: {yes_votes} votes\nNo: {no_votes} votes")

    @commands.guild_only()
    @commands.command()
    async def accept(self, ctx, member: discord.Member, role_name: str):
        """Accept an application and assign a role."""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            return await ctx.send("Role not found.")

        applications = await self.config.guild(ctx.guild).applications()
        if str(role.id) in applications and str(member.id) in applications[str(role.id)]:
            await member.add_roles(role)
            embed = discord.Embed(title="Staff Hired", color=discord.Color.green())
            embed.add_field(name="Username", value=member.name, inline=False)
            embed.add_field(name="User ID", value=member.id, inline=False)
            embed.add_field(name="Position", value=role.name, inline=False)
            embed.add_field(name="Issuer", value=ctx.author.name, inline=False)
            staff_updates_channel_id = await self.config.guild(ctx.guild).staff_updates_channel()
            staff_updates_channel = self.bot.get_channel(staff_updates_channel_id)
            if staff_updates_channel:
                await staff_updates_channel.send(embed=embed)
            await member.send(f"Congratulations! Your application for {role.name} has been accepted.")
            await ctx.send(f"Accepted {member.display_name} for {role.name}.")
        else:
            await ctx.send("No application found for this member and role.")

    @commands.guild_only()
    @commands.command()
    async def deny(self, ctx, member: discord.Member, role_name: str):
        """Deny an application and send a denial message."""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            return await ctx.send("Role not found.")

        applications = await self.config.guild(ctx.guild).applications()
        if str(role.id) in applications and str(member.id) in applications[str(role.id)]:
            await member.send(f"Sorry, your application for {role.name} was denied.")
            await ctx.send(f"Denied {member.display_name}'s application for {role.name}.")
        else:
            await ctx.send("No application found for this member and role.")

    @commands.guild_only()
    @commands.command()
    async def remq(self, ctx, role: discord.Role, *, question: str):
        """Remove a question for a specific role."""
        async with self.config.guild(ctx.guild).questions() as questions:
            if question in questions.get(str(role.id), []):
                questions[str(role.id)].remove(question)
                await ctx.send(f"Question removed for {role.name}.")
            else:
                await ctx.send("Question not found for this role.")

    @commands.guild_only()
    @commands.command()
    async def clearqs(self, ctx, role: discord.Role):
        """Clear all questions for a specific role."""
        async with self.config.guild(ctx.guild).questions() as questions:
            if str(role.id) in questions:
                del questions[str(role.id)]
                await ctx.send(f"Questions cleared for {role.name}.")
            else:
                await ctx.send("No questions set for this role.")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def setupdates(self, ctx, channel: discord.TextChannel):
        """Set the channel for staff update messages."""
        await self.config.guild(ctx.guild).staff_updates_channel.set(channel.id)
        await ctx.send(f"Staff updates channel set to {channel.mention}")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def setblacklist(self, ctx, channel: discord.TextChannel):
        """Set the channel for blacklist messages."""
        await self.config.guild(ctx.guild).blacklist_channel.set(channel.id)
        await ctx.send(f"Blacklist channel set to {channel.mention}")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Handle command errors."""
        if isinstance(error, commands.CheckFailure):
            await ctx.send("You do not have the required permissions to use this command.")

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
        staff_updates_channel_id = await self.config.guild(ctx.guild).staff_updates_channel()
        staff_updates_channel = self.bot.get_channel(staff_updates_channel_id)
        if staff_updates_channel:
            await staff_updates_channel.send(embed=embed)
        await ctx.send(f"Fired {member.name} from {role.name}.")

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
        staff_updates_channel_id = await self.config.guild(ctx.guild).staff_updates_channel()
        staff_updates_channel = self.bot.get_channel(staff_updates_channel_id)
        if staff_updates_channel:
            await staff_updates_channel.send(embed=embed)
        await ctx.send(f"Demoted {member.name} from {old_role.name} to {new_role.name}.")

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
        staff_updates_channel_id = await self.config.guild(ctx.guild).staff_updates_channel()
        staff_updates_channel = self.bot.get_channel(staff_updates_channel_id)
        if staff_updates_channel:
            await staff_updates_channel.send(embed=embed)
        await ctx.send(f"Promoted {member.name} from {old_role.name} to {new_role.name}.")

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
        blacklist_channel_id = await self.config.guild(ctx.guild).blacklist_channel()
        blacklist_channel = self.bot.get_channel(blacklist_channel_id)
        if blacklist_channel:
            await blacklist_channel.send(embed=embed)
        await ctx.send(f"Blacklisted {member.name} for {reason}.")

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
        await self.config.guild(ctx.guild).loa_requests_channel.set(channel.id)
        await ctx.send(f"LOA requests channel set to {channel.mention}")

    @loa.command()
    @commands.has_permissions(manage_roles=True)
    async def role(self, ctx, role: discord.Role):
        """Set the role to be assigned during LOA."""
        await self.config.guild(ctx.guild).loa_role.set(role.id)
        await ctx.send(f"LOA role set to {role.name}")

    @loa.command()
    async def request(self, ctx, duration: str, reason: str):
        """Request a leave of absence."""
        async with self.config.guild(ctx.guild).loa_requests() as loa_requests:
            loa_requests[ctx.author.id] = {
                "user": ctx.author.id,
                "duration": duration,
                "reason": reason,
                "approved_by": None
            }

        loa_requests_channel_id = await self.config.guild(ctx.guild).loa_requests_channel()
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
        async with self.config.guild(ctx.guild).loa_requests() as loa_requests:
            if user_id in loa_requests and loa_requests[user_id]["approved_by"] is None:
                loa_requests[user_id]["approved_by"] = ctx.author.id
                user = self.bot.get_user(loa_requests[user_id]["user"])
                loa_role_id = await self.config.guild(ctx.guild).loa_role()
                loa_role = ctx.guild.get_role(loa_role_id)
                if loa_role:
                    await user.add_roles(loa_role)
                embed = discord.Embed(title="Leave of Absence", color=discord.Color.green())
                embed.add_field(name="User", value=user.name, inline=False)
                embed.add_field(name="Duration", value=loa_requests[user_id]["duration"], inline=False)
                embed.add_field(name="Reason", value=loa_requests[user_id]["reason"], inline=False)
                embed.add_field(name="Approved by", value=ctx.author.name, inline=False)
                staff_updates_channel_id = await self.config.guild(ctx.guild).staff_updates_channel()
                staff_updates_channel = self.bot.get_channel(staff_updates_channel_id)
                if staff_updates_channel:
                    await staff_updates_channel.send(embed=embed)
                await ctx.send(f"Leave of Absence request for {user.name} approved.")
            else:
                await ctx.send(f"Leave of Absence request for user ID {user_id} not found or already approved.")

    @loa.command()
    async def deny(self, ctx, user_id: int):
        """Deny a leave of absence request."""
        async with self.config.guild(ctx.guild).loa_requests() as loa_requests:
            if user_id in loa_requests:
                del loa_requests[user_id]
                await ctx.send(f"Leave of Absence request for user ID {user_id} denied and removed.")
            else:
                await ctx.send(f"Leave of Absence request for user ID {user_id} not found.")

    @loa.command()
    async def end(self, ctx, user_id: int):
        """End a leave of absence."""
        async with self.config.guild(ctx.guild).loa_requests() as loa_requests:
            if user_id in loa_requests and loa_requests[user_id]["approved_by"] is not None:
                user = self.bot.get_user(loa_requests[user_id]["user"])
                loa_role_id = await self.config.guild(ctx.guild).loa_role()
                loa_role = ctx.guild.get_role(loa_role_id)
                if loa_role:
                    await user.remove_roles(loa_role)
                del loa_requests[user_id]
                embed = discord.Embed(title="Leave of Absence Ended", color=discord.Color.red())
                embed.add_field(name="User", value=user.name, inline=False)
                embed.add_field(name="User ID", value=user.id, inline=False)
                staff_updates_channel_id = await self.config.guild(ctx.guild).staff_updates_channel()
                staff_updates_channel = self.bot.get_channel(staff_updates_channel_id)
                if staff_updates_channel:
                    await staff_updates_channel.send(embed=embed)
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
        async with self.config.guild(ctx.guild).resignation_requests() as resignation_requests:
            resignation_requests[ctx.author.id] = {
                "user": ctx.author.id,
                "reason": reason,
                "approved_by": None
            }

        resignation_requests_channel_id = await self.config.guild(ctx.guild).resignation_requests_channel()
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
        async with self.config.guild(ctx.guild).resignation_requests() as resignation_requests:
            if user_id in resignation_requests and resignation_requests[user_id]["approved_by"] is None:
                resignation_requests[user_id]["approved_by"] = ctx.author.id
                user = self.bot.get_user(resignation_requests[user_id]["user"])
                embed = discord.Embed(title="Staff Member Resigned", color=discord.Color.red())
                embed.add_field(name="Former Staff", value=user.name, inline=False)
                embed.add_field(name="Reason", value=resignation_requests[user_id]["reason"], inline=False)
                embed.add_field(name="Approved by", value=ctx.author.name, inline=False)
                staff_updates_channel_id = await self.config.guild(ctx.guild).staff_updates_channel()
                staff_updates_channel = self.bot.get_channel(staff_updates_channel_id)
                if staff_updates_channel:
                    await staff_updates_channel.send(embed=embed)
                await ctx.send(f"Resignation request for {user.name} accepted.")
            else:
                await ctx.send(f"Resignation request for user ID {user_id} not found or already accepted.")

    @resign.command()
    async def deny(self, ctx, user_id: int):
        """Deny a resignation request."""
        async with self.config.guild(ctx.guild).resignation_requests() as resignation_requests:
            if user_id in resignation_requests:
                del resignation_requests[user_id]
                await ctx.send(f"Resignation request for user ID {user_id} denied and removed.")
            else:
                await ctx.send(f"Resignation request for user ID {user_id} not found.")

    @resign.command()
    @commands.has_permissions(manage_channels=True)
    async def channel(self, ctx, channel: discord.TextChannel):
        """Set the channel for resignation request messages."""
        await self.config.guild(ctx.guild).resignation_requests_channel.set(channel.id)
        await ctx.send(f"Resignation requests channel set to {channel.mention}")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Handle reactions for application voting."""
        if payload.user_id == self.bot.user.id:
            return

        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        if message.author != self.bot.user or not message.embeds:
            return

        embed = message.embeds[0]
        if embed.title.startswith("New Application for"):
            if payload.emoji.name == "✅" or payload.emoji.name == "❌":
                # Add the reaction to the tally
                await self.add_vote(payload.message_id, payload.emoji.name)

    async def add_vote(self, message_id, emoji):
        """Add a vote to the tally."""
        async with self.config.guild_from_id(payload.guild_id).applications() as applications:
            if str(message_id) not in applications:
                applications[str(message_id)] = {"✅": 0, "❌": 0}
            applications[str(message_id)][emoji] += 1

    async def tally_votes(self, poll_message, channel):
        await asyncio.sleep(14400)  # 4 hours in seconds
        poll_message = await poll_message.channel.fetch_message(poll_message.id)
        async with self.config.guild_from_id(poll_message.guild.id).applications() as applications:
            votes = applications.get(str(poll_message.id), {"✅": 0, "❌": 0})
            yes_votes = votes["✅"]
            no_votes = votes["❌"]
            await channel.send(f"Voting has ended. Results:\nYes: {yes_votes} votes\nNo: {no_votes} votes")

def setup(bot):
    bot.add_cog(StaffApps(bot))
