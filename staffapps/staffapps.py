import discord
import asyncio
from redbot.core import commands, Config
from .dashboard_integration import DashboardIntegration

class StaffApps(DashboardIntegration, commands.Cog):  # Subclass ``DashboardIntegration``.
    """Cog for handling applications and managing staff members."""

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
            "resignation_requests": {},
            "role_categories": {},
            "base_role": None,
            "auto_role": None
        }
        self.config.register_guild(**default_guild)

    # Application Commands
    @commands.guild_only()
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def addq(self, ctx, role: discord.Role, *, question: str):
        """Add a question for a specific role."""
        async with self.config.guild(ctx.guild).questions() as questions:
            questions.setdefault(str(role.id), []).append(question)
        await ctx.send(f"Question added for {role.name}.")

    @commands.guild_only()
    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def setappchannel(self, ctx, channel: discord.TextChannel):
        """Set the application channel."""
        await self.config.guild(ctx.guild).application_channel.set(channel.id)
        await ctx.send(f"Application channel set to {channel.mention}.")

    @commands.guild_only()
    @commands.command()
    async def listroles(self, ctx):
        """List roles available for application."""
        questions = await self.config.guild(ctx.guild).questions()
        roles = [ctx.guild.get_role(int(role_id)).mention for role_id in questions if ctx.guild.get_role(int(role_id))]
        if roles:
            roles_list = '\n'.join(roles)
            await ctx.send("Roles available for application:\n{}\n\nUse `apply <role_mention>` to apply for a role.".format(roles_list))
        else:
            await ctx.send("No roles set for applications.")

    @commands.guild_only()
    @commands.command()
    async def apply(self, ctx, *, role: discord.Role):
        """Apply for a specific role."""
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
            embed.add_field(name="Status", value="Pending", inline=False)
            message = await application_channel.send(embed=embed)
            async with self.config.guild(ctx.guild).applications() as applications:
                applications[str(role.id)][str(ctx.author.id)]["message_id"] = message.id
            await ctx.author.send("Application submitted. Thank you!")
        else:
            await ctx.author.send("Application channel not set. Please set an application channel using the `setappchannel` command.")

    @commands.guild_only()
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def remq(self, ctx, role: discord.Role, *, question: str):
        """Remove a question for a specific role."""
        async with self.config.guild(ctx.guild).questions() as questions:
            if question in questions.get(str(role.id), []):
                questions[str(role.id)].remove(question)
                await ctx.send(f"Question removed for {role.mention}.")
            else:
                await ctx.send("Question not found for this role.")

    @commands.guild_only()
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def clearqs(self, ctx, role: discord.Role):
        """Clear all questions for a specific role."""
        async with self.config.guild(ctx.guild).questions() as questions:
            if str(role.id) in questions:
                del questions[str(role.id)]
                await ctx.send(f"Questions cleared for {role.mention}.")
            else:
                await ctx.send("No questions set for this role.")

    # Staff Management Commands
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
            await ctx.send("You do not have the required permissions to run this command.")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def fire(self, ctx, member: discord.Member, role: discord.Role):
        """Fire a staff member."""
        await member.remove_roles(role)
        auto_role_id = await self.config.guild(ctx.guild).auto_role()
        if auto_role_id:
            auto_role = ctx.guild.get_role(auto_role_id)
            if auto_role:
                await member.remove_roles(auto_role)
        embed = discord.Embed(title="Staff Fired", color=discord.Color.red())
        embed.add_field(name="Username", value=member.name, inline=False)
        embed.add_field(name="User ID", value=member.id, inline=False)
        embed.add_field(name="Position", value=role.mention, inline=False)
        embed.add_field(name="Issuer", value=ctx.author.name, inline=False)
        staff_updates_channel_id = await self.config.guild(ctx.guild).staff_updates_channel()
        staff_updates_channel = self.bot.get_channel(staff_updates_channel_id)
        if staff_updates_channel:
            await staff_updates_channel.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def demote(self, ctx, member: discord.Member, new_role: discord.Role = None):
        """Demote a staff member."""
        role_categories = await self.config.guild(ctx.guild).role_categories()
        member_roles = [role for role in member.roles if role.id in [int(role_id) for roles in role_categories.values() for role_id in roles]]

        if not member_roles:
            return await ctx.send("This member does not have any staff role that can be demoted.")

        current_role = sorted(member_roles, key=lambda r: r.position, reverse=True)[0]
        category_name = next((cat for cat, roles in role_categories.items() if str(current_role.id) in roles), None)
        if not category_name:
            return await ctx.send("This role is not part of any configured category.")

        roles_in_category = role_categories[category_name]
        current_index = roles_in_category.index(str(current_role.id))

        if new_role:
            if str(new_role.id) not in roles_in_category:
                return await ctx.send("The specified new role is not part of the same category.")
        else:
            if current_index == 0:
                return await ctx.send("This member is already at the lowest role in the category.")
            new_role = ctx.guild.get_role(int(roles_in_category[current_index - 1]))

        await member.remove_roles(current_role)
        await member.add_roles(new_role)

        # Handle category role switch
        new_category_name = next((cat for cat, roles in role_categories.items() if str(new_role.id) in roles), None)
        if new_category_name and new_category_name != category_name:
            old_category_role = ctx.guild.get_role(int(role_categories[category_name][0]))
            new_category_role = ctx.guild.get_role(int(role_categories[new_category_name][0]))
            if old_category_role:
                await member.remove_roles(old_category_role)
            if new_category_role:
                await member.add_roles(new_category_role)

        embed = discord.Embed(title="Staff Demoted", color=discord.Color.orange())
        embed.add_field(name="Username", value=member.name, inline=False)
        embed.add_field(name="User ID", value=member.id, inline=False)
        embed.add_field(name="New Position", value=new_role.mention, inline=False)
        embed.add_field(name="Old Position", value=current_role.mention, inline=False)
        embed.add_field(name="Issuer", value=ctx.author.name, inline=False)
        staff_updates_channel_id = await self.config.guild(ctx.guild).staff_updates_channel()
        staff_updates_channel = self.bot.get_channel(staff_updates_channel_id)
        if staff_updates_channel:
            await staff_updates_channel.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def promote(self, ctx, member: discord.Member, new_role: discord.Role = None):
        """Promote a staff member."""
        role_categories = await self.config.guild(ctx.guild).role_categories()
        member_roles = [role for role in member.roles if role.id in [int(role_id) for roles in role_categories.values() for role_id in roles]]

        if not member_roles:
            return await ctx.send("This member does not have any staff role that can be promoted.")

        current_role = sorted(member_roles, key=lambda r: r.position, reverse=True)[0]
        category_name = next((cat for cat, roles in role_categories.items() if str(current_role.id) in roles), None)
        if not category_name:
            return await ctx.send("This role is not part of any configured category.")

        roles_in_category = role_categories[category_name]
        current_index = roles_in_category.index(str(current_role.id))

        if new_role:
            if str(new_role.id) not in roles_in_category:
                return await ctx.send("The specified new role is not part of the same category.")
        else:
            if current_index == len(roles_in_category) - 1:
                return await ctx.send("This member is already at the highest role in the category.")
            new_role = ctx.guild.get_role(int(roles_in_category[current_index + 1]))

        await member.remove_roles(current_role)
        await member.add_roles(new_role)

        # Handle category role switch
        new_category_name = next((cat for cat, roles in role_categories.items() if str(new_role.id) in roles), None)
        if new_category_name and new_category_name != category_name:
            old_category_role = ctx.guild.get_role(int(role_categories[category_name][0]))
            new_category_role = ctx.guild.get_role(int(role_categories[new_category_name][0]))
            if old_category_role:
                await member.remove_roles(old_category_role)
            if new_category_role:
                await member.add_roles(new_category_role)

        embed = discord.Embed(title="Staff Promoted", color=discord.Color.blue())
        embed.add_field(name="Username", value=member.name, inline=False)
        embed.add_field(name="User ID", value=member.id, inline=False)
        embed.add_field(name="New Position", value=new_role.mention, inline=False)
        embed.add_field(name="Old Position", value=current_role.mention, inline=False)
        embed.add_field(name="Issuer", value=ctx.author.name, inline=False)
        staff_updates_channel_id = await self.config.guild(ctx.guild).staff_updates_channel()
        staff_updates_channel = self.bot.get_channel(staff_updates_channel_id)
        if staff_updates_channel:
            await staff_updates_channel.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def setcategory(self, ctx, category_name: str):
        """Set a new role category."""
        async with self.config.guild(ctx.guild).role_categories() as role_categories:
            if category_name in role_categories:
                return await ctx.send("This category already exists.")
            role_categories[category_name] = []
        await ctx.send(f"Category '{category_name}' created.")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def roleadd(self, ctx, category_name: str, role: discord.Role):
        """Add a role to a category."""
        async with self.config.guild(ctx.guild).role_categories() as role_categories:
            if category_name not in role_categories:
                return await ctx.send("This category does not exist.")
            if str(role.id) in role_categories[category_name]:
                return await ctx.send("This role is already in the category.")
            role_categories[category_name].append(str(role.id))
        await ctx.send(f"Role {role.mention} added to category '{category_name}'.")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def rolerem(self, ctx, category_name: str, role: discord.Role):
        """Remove a role from a category."""
        async with self.config.guild(ctx.guild).role_categories() as role_categories:
            if category_name not in role_categories:
                return await ctx.send("This category does not exist.")
            if str(role.id) not in role_categories[category_name]:
                return await ctx.send("This role is not in the category.")
            role_categories[category_name].remove(str(role.id))
        await ctx.send(f"Role {role.mention} removed from category '{category_name}'.")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def setautorole(self, ctx, role: discord.Role):
        """Set the automatically configured role given upon hiring."""
        await self.config.guild(ctx.guild).auto_role.set(role.id)
        await ctx.send(f"Automatically configured role set to {role.mention}.")

    # LOA Commands
    @commands.group()
    @commands.has_permissions(send_messages=True)
    async def loa(self, ctx):
        """Group command for managing leave of absence requests."""
        pass

    @loa.command(name="setchannel")
    @commands.has_permissions(manage_channels=True)
    async def loa_setchannel(self, ctx, channel: discord.TextChannel):
        """Set the channel for LOA request messages."""
        await self.config.guild(ctx.guild).loa_requests_channel.set(channel.id)
        await ctx.send(f"LOA requests channel set to {channel.mention}")

    @loa.command(name="role")
    @commands.has_permissions(manage_roles=True)
    async def loa_role(self, ctx, role: discord.Role):
        """Set the role to be assigned during LOA."""
        await self.config.guild(ctx.guild).loa_role.set(role.id)
        await ctx.send(f"LOA role set to {role.mention}")

    @loa.command(name="request")
    async def loa_request(self, ctx, duration: str, reason: str):
        """Request a leave of absence."""
        loa_requests = await self.config.guild(ctx.guild).loa_requests()
        user_id = ctx.author.id
        loa_requests[user_id] = {
            "user": ctx.author.id,
            "duration": duration,
            "reason": reason,
            "approved_by": None
        }
        await self.config.guild(ctx.guild).loa_requests.set(loa_requests)

        loa_requests_channel_id = await self.config.guild(ctx.guild).loa_requests_channel()
        loa_requests_channel = self.bot.get_channel(loa_requests_channel_id)
        if loa_requests_channel:
            embed = discord.Embed(title="LOA Request", color=discord.Color.yellow())
            embed.add_field(name="User", value=ctx.author.name, inline=False)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Duration", value=duration, inline=False)
            embed.add_field(name="User ID", value=ctx.author.id, inline=False)
            embed.add_field(name="Status", value="Pending", inline=False)
            embed.set_footer(text="Do `app accept loa <user_id>` or `app deny loa <user_id>`")
            message = await loa_requests_channel.send(embed=embed)
            loa_requests[user_id]["message_id"] = message.id

        await ctx.send(f"Leave of Absence request submitted for {duration} due to {reason}.")

    @loa.command(name="end")
    async def loa_end(self, ctx, user_id: int):
        """End a leave of absence."""
        loa_requests = await self.config.guild(ctx.guild).loa_requests()
        if user_id in loa_requests and loa_requests[user_id]["approved_by"] is not None:
            user = self.bot.get_user(loa_requests[user_id]["user"])
            loa_role_id = await self.config.guild(ctx.guild).loa_role()
            loa_role = ctx.guild.get_role(loa_role_id)
            if loa_role:
                await user.remove_roles(loa_role)
            del loa_requests[user_id]
            await self.config.guild(ctx.guild).loa_requests.set(loa_requests)
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

    # Resignation Commands
    @commands.group()
    @commands.has_permissions(send_messages=True)
    async def resign(self, ctx):
        """Group command for managing resignation requests."""
        pass

    @resign.command(name="request")
    async def resign_request(self, ctx, reason: str):
        """Request a resignation."""
        resignation_requests = await self.config.guild(ctx.guild).resignation_requests()
        user_id = ctx.author.id
        resignation_requests[user_id] = {
            "user": ctx.author.id,
            "reason": reason,
            "approved_by": None
        }
        await self.config.guild(ctx.guild).resignation_requests.set(resignation_requests)

        resignation_requests_channel_id = await self.config.guild(ctx.guild).resignation_requests_channel()
        resignation_requests_channel = self.bot.get_channel(resignation_requests_channel_id)
        if resignation_requests_channel:
            embed = discord.Embed(title="Resignation Request", color=discord.Color.yellow())
            embed.add_field(name="User", value=ctx.author.name, inline=False)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="User ID", value=ctx.author.id, inline=False)
            embed.add_field(name="Status", value="Pending", inline=False)
            embed.set_footer(text="Do `app accept resignation <user_id>` or `app deny resignation <user_id>`")
            message = await resignation_requests_channel.send(embed=embed)
            resignation_requests[user_id]["message_id"] = message.id

        await ctx.send(f"Resignation request submitted due to {reason}.")

    @resign.command(name="setchannel")
    @commands.has_permissions(manage_channels=True)
    async def resign_setchannel(self, ctx, channel: discord.TextChannel):
        """Set the channel for resignation request messages."""
        await self.config.guild(ctx.guild).resignation_requests_channel.set(channel.id)
        await ctx.send(f"Resignation requests channel set to {channel.mention}")

    # App Commands
    @commands.group()
    async def app(self, ctx):
        """Group command for managing applications, LOA, and resignations."""
        pass

    @app.command()
    async def status(self, ctx, request_type: str):
        """Check the status of your application, LOA, or resignation."""
        if request_type.lower() == "application":
            applications = await self.config.guild(ctx.guild).applications()
            for role_id, role_apps in applications.items():
                if str(ctx.author.id) in role_apps:
                    role = ctx.guild.get_role(int(role_id))
                    await ctx.send(f"Your application status for role {role.mention}: pending")
                    return
            await ctx.send("You have no pending applications.")
        elif request_type.lower() == "loa":
            loa_requests = await self.config.guild(ctx.guild).loa_requests()
            if str(ctx.author.id) in loa_requests:
                loa_request = loa_requests[str(ctx.author.id)]
                status = "approved" if loa_request["approved_by"] else "pending"
                await ctx.send(f"Your leave of absence status: {status}")
            else:
                await ctx.send("You have no pending leave of absence requests.")
        elif request_type.lower() == "resignation":
            resignation_requests = await self.config.guild(ctx.guild).resignation_requests()
            if str(ctx.author.id) in resignation_requests:
                resignation_request = resignation_requests[str(ctx.author.id)]
                status = "approved" if resignation_request["approved_by"] else "pending"
                await ctx.send(f"Your resignation status: {status}")
            else:
                await ctx.send("You have no pending resignation requests.")
        else:
            await ctx.send("Invalid request type. Use 'application', 'loa', or 'resignation'.")

    @app.command()
    @commands.has_permissions(manage_roles=True)
    async def accept(self, ctx, request_type: str, user_id: int):
        """Accept an application, LOA, or resignation request."""
        if request_type.lower() == "application":
            applications = await self.config.guild(ctx.guild).applications()
            for role_id, role_apps in applications.items():
                if str(user_id) in role_apps:
                    member = ctx.guild.get_member(user_id)
                    role = ctx.guild.get_role(int(role_id))
                    if not role:
                        return await ctx.send(f"Role {role_id} not found.")
                    await member.add_roles(role)
                    auto_role_id = await self.config.guild(ctx.guild).auto_role()
                    if auto_role_id:
                        auto_role = ctx.guild.get_role(auto_role_id)
                        if auto_role:
                            await member.add_roles(auto_role)
                    await member.send(f"Congratulations! Your application for {role.mention} has been accepted.")
                    embed = discord.Embed(title="Staff Hired", color=discord.Color.green())
                    embed.add_field(name="Username", value=member.name, inline=False)
                    embed.add_field(name="User ID", value=member.id, inline=False)
                    embed.add_field(name="Position", value=role.mention, inline=False)
                    embed.add_field(name="Issuer", value=ctx.author.name, inline=False)
                    staff_updates_channel_id = await self.config.guild(ctx.guild).staff_updates_channel()
                    staff_updates_channel = self.bot.get_channel(staff_updates_channel_id)
                    if staff_updates_channel:
                        await staff_updates_channel.send(embed=embed)
                    # Update the original application message
                    message_id = role_apps[str(user_id)].get("message_id")
                    if message_id:
                        application_channel_id = await self.config.guild(ctx.guild).application_channel()
                        application_channel = self.bot.get_channel(application_channel_id)
                        message = await application_channel.fetch_message(message_id)
                        if message:
                            embed = message.embeds[0]
                            embed.set_field_at(-1, name="Status", value="Approved", inline=False)
                            await message.edit(embed=embed)

                    await ctx.send(f"Accepted {member.display_name} for {role.mention}.")
                    return
            await ctx.send("No application found for this member and role.")
        elif request_type.lower() == "loa":
            loa_requests = await self.config.guild(ctx.guild).loa_requests()
            if user_id in loa_requests and loa_requests[user_id]["approved_by"] is None:
                loa_requests[user_id]["approved_by"] = ctx.author.id
                await self.config.guild(ctx.guild).loa_requests.set(loa_requests)
                user = self.bot.get_user(loa_requests[user_id]["user"])
                loa_role_id = await self.config.guild(ctx.guild).loa_role()
                loa_role = ctx.guild.get_role(loa_role_id)
                if not loa_role:
                    return await ctx.send("LOA role not found.")
                await user.add_roles(loa_role)
                embed = discord.Embed(title="Leave of Absence", color=discord.Color.green())
                embed.add_field(name="User", value=user.name, inline=False)
                embed.add_field(name="Duration", value=loa_requests[user_id]["duration"], inline=False)
                embed.add_field(name="Reason", value=loa_requests[user_id]["reason"], inline=False)
                embed.add_field(name="Approved by", value=ctx.author.name, inline=False)
                embed.add_field(name="Status", value="Approved", inline=False)
                staff_updates_channel_id = await self.config.guild(ctx.guild).staff_updates_channel()
                staff_updates_channel = self.bot.get_channel(staff_updates_channel_id)
                if staff_updates_channel:
                    await staff_updates_channel.send(embed=embed)

                # Update the original LOA request message
                message_id = loa_requests[user_id].get("message_id")
                if message_id:
                    loa_requests_channel_id = await self.config.guild(ctx.guild).loa_requests_channel()
                    loa_requests_channel = self.bot.get_channel(loa_requests_channel_id)
                    message = await loa_requests_channel.fetch_message(message_id)
                    if message:
                        embed = message.embeds[0]
                        embed.set_field_at(-1, name="Status", value="Approved", inline=False)
                        await message.edit(embed=embed)

                await ctx.send(f"Leave of Absence request for {user.name} approved.")
            else:
                await ctx.send(f"Leave of Absence request for user ID {user_id} not found or already approved.")
        elif request_type.lower() == "resignation":
            resignation_requests = await self.config.guild(ctx.guild).resignation_requests()
            if user_id in resignation_requests and resignation_requests[user_id]["approved_by"] is None:
                resignation_requests[user_id]["approved_by"] = ctx.author.id
                await self.config.guild(ctx.guild).resignation_requests.set(resignation_requests)
                user = self.bot.get_user(resignation_requests[user_id]["user"])
                embed = discord.Embed(title="Staff Member Resigned", color=discord.Color.red())
                embed.add_field(name="Former Staff", value=user.name, inline=False)
                embed.add_field(name="Reason", value=resignation_requests[user_id]["reason"], inline=False)
                embed.add_field(name="Approved by", value=ctx.author.name, inline=False)
                embed.add_field(name="Status", value="Approved", inline=False)
                staff_updates_channel_id = await self.config.guild(ctx.guild).staff_updates_channel()
                staff_updates_channel = self.bot.get_channel(staff_updates_channel_id)
                if staff_updates_channel:
                    await staff_updates_channel.send(embed=embed)

                # Update the original resignation request message
                message_id = resignation_requests[user_id].get("message_id")
                if message_id:
                    resignation_requests_channel_id = await self.config.guild(ctx.guild).resignation_requests_channel()
                    resignation_requests_channel = self.bot.get_channel(resignation_requests_channel_id)
                    message = await resignation_requests_channel.fetch_message(message_id)
                    if message:
                        embed = message.embeds[0]
                        embed.set_field_at(-1, name="Status", value="Approved", inline=False)
                        await message.edit(embed=embed)

                await ctx.send(f"Resignation request for {user.name} accepted.")
            else:
                await ctx.send(f"Resignation request for user ID {user_id} not found or already accepted.")
        else:
            await ctx.send("Invalid request type. Use 'application', 'loa', or 'resignation'.")

    @app.command()
    @commands.has_permissions(manage_roles=True)
    async def deny(self, ctx, request_type: str, user_id: int):
        """Deny an application, LOA, or resignation request."""
        if request_type.lower() == "application":
            applications = await self.config.guild(ctx.guild).applications()
            for role_id, role_apps in applications.items():
                if str(user_id) in role_apps:
                    member = ctx.guild.get_member(user_id)
                    await member.send(f"Sorry, your application for role {ctx.guild.get_role(int(role_id)).mention} was denied.")
                    await ctx.send(f"Denied {member.display_name}'s application for role {ctx.guild.get_role(int(role_id)).mention}.")

                    # Update the original application message
                    message_id = role_apps[str(user_id)].get("message_id")
                    if message_id:
                        application_channel_id = await self.config.guild(ctx.guild).application_channel()
                        application_channel = self.bot.get_channel(application_channel_id)
                        message = await application_channel.fetch_message(message_id)
                        if message:
                            embed = message.embeds[0]
                            embed.set_field_at(-1, name="Status", value="Denied", inline=False)
                            await message.edit(embed=embed)

                    return
            await ctx.send("No application found for this member and role.")
        elif request_type.lower() == "loa":
            loa_requests = await self.config.guild(ctx.guild).loa_requests()
            if user_id in loa_requests:
                loa_requests[user_id]["approved_by"] = None
                await self.config.guild(ctx.guild).loa_requests.set(loa_requests)
                embed = discord.Embed(title="Leave of Absence", color=discord.Color.red())
                embed.add_field(name="User ID", value=user_id, inline=False)
                embed.add_field(name="Status", value="Denied", inline=False)
                staff_updates_channel_id = await self.config.guild(ctx.guild).staff_updates_channel()
                staff_updates_channel = self.bot.get_channel(staff_updates_channel_id)
                if staff_updates_channel:
                    await staff_updates_channel.send(embed=embed)

                # Update the original LOA request message
                message_id = loa_requests[user_id].get("message_id")
                if message_id:
                    loa_requests_channel_id = await self.config.guild(ctx.guild).loa_requests_channel()
                    loa_requests_channel = self.bot.get_channel(loa_requests_channel_id)
                    message = await loa_requests_channel.fetch_message(message_id)
                    if message:
                        embed = message.embeds[0]
                        embed.set_field_at(-1, name="Status", value="Denied", inline=False)
                        await message.edit(embed=embed)

                await ctx.send(f"Leave of Absence request for user ID {user_id} denied.")
            else:
                await ctx.send(f"Leave of Absence request for user ID {user_id} not found.")
        elif request_type.lower() == "resignation":
            resignation_requests = await self.config.guild(ctx.guild).resignation_requests()
            if user_id in resignation_requests:
                resignation_requests[user_id]["approved_by"] = None
                await self.config.guild(ctx.guild).resignation_requests.set(resignation_requests)
                embed = discord.Embed(title="Resignation Request", color=discord.Color.red())
                embed.add_field(name="User ID", value=user_id, inline=False)
                embed.add_field(name="Status", value="Denied", inline=False)
                staff_updates_channel_id = await self.config.guild(ctx.guild).staff_updates_channel()
                staff_updates_channel = self.bot.get_channel(staff_updates_channel_id)
                if staff_updates_channel:
                    await staff_updates_channel.send(embed=embed)

                # Update the original resignation request message
                message_id = resignation_requests[user_id].get("message_id")
                if message_id:
                    resignation_requests_channel_id = await self.config.guild(ctx.guild).resignation_requests_channel()
                    resignation_requests_channel = self.bot.get_channel(resignation_requests_channel_id)
                    message = await resignation_requests_channel.fetch_message(message_id)
                    if message:
                        embed = message.embeds[0]
                        embed.set_field_at(-1, name="Status", value="Denied", inline=False)
                        await message.edit(embed=embed)

                await ctx.send(f"Resignation request for user ID {user_id} denied.")
            else:
                await ctx.send(f"Resignation request for user ID {user_id} not found.")
        else:
            await ctx.send("Invalid request type. Use 'application', 'loa', or 'resignation'.")
