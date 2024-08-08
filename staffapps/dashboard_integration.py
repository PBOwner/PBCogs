from redbot.core import commands
from redbot.core.bot import Red
import discord
import typing

def dashboard_page(*args, **kwargs):  # This decorator is required because the cog Dashboard may load after the third party when the bot is started.
    def decorator(func: typing.Callable):
        func.__dashboard_decorator_params__ = (args, kwargs)
        return func
    return decorator

class DashboardIntegration:
    bot: Red

    @commands.Cog.listener()
    async def on_dashboard_cog_add(self, dashboard_cog: commands.Cog) -> None:  # ``on_dashboard_cog_add`` is triggered by the Dashboard cog automatically.
        dashboard_cog.rpc.third_parties_handler.add_third_party(self)  # Add the third party to Dashboard.

    @dashboard_page(name="manage_questions", description="Manage the questions for staff applications.", methods=("GET", "POST"), is_owner=True)
    async def manage_questions_page(self, user: discord.User, guild: discord.Guild, **kwargs) -> typing.Dict[str, typing.Any]:
        import wtforms
        class Form(kwargs["Form"]):
            def __init__(self):
                super().__init__(prefix="manage_questions_form_")
            role: wtforms.IntegerField = wtforms.IntegerField("Role ID:", validators=[wtforms.validators.InputRequired(), kwargs["DpyObjectConverter"](discord.Role)])
            question: wtforms.StringField = wtforms.StringField("Question:", validators=[wtforms.validators.InputRequired()])
            action: wtforms.SelectField = wtforms.SelectField("Action:", choices=[("add", "Add"), ("remove", "Remove"), ("clear", "Clear All")])
            index: wtforms.IntegerField = wtforms.IntegerField("Index (for remove action):", validators=[wtforms.validators.Optional()])
            submit: wtforms.SubmitField = wtforms.SubmitField("Update Questions")

        form: Form = Form()
        if form.validate_on_submit() and await form.validate_dpy_converters():
            role = form.role.data
            question = form.question.data
            action = form.action.data
            index = form.index.data
            async with self.config.guild(guild).questions() as questions:
                if action == "add":
                    questions.setdefault(str(role.id), []).append(question)
                    message = f"Question added for {role.name}."
                    category = "success"
                elif action == "remove":
                    if 0 < index <= len(questions.get(str(role.id), [])):
                        removed_question = questions[str(role.id)].pop(index - 1)
                        message = f"Removed question: {removed_question}"
                        category = "success"
                    else:
                        message = "Invalid question index."
                        category = "error"
                elif action == "clear":
                    if str(role.id) in questions:
                        del questions[str(role.id)]
                        message = f"Questions cleared for {role.name}."
                        category = "success"
                    else:
                        message = "No questions set for this role."
                        category = "error"
            return {
                "status": 0,
                "notifications": [{"message": message, "category": category}],
                "redirect_url": kwargs["request_url"],
            }

        source = "{{ form|safe }}"

        return {
            "status": 0,
            "web_content": {"source": source, "form": form},
        }

    @dashboard_page(name="manage_channel", description="Set the application channel.", methods=("GET", "POST"), is_owner=True)
    async def manage_channel_page(self, user: discord.User, guild: discord.Guild, **kwargs) -> typing.Dict[str, typing.Any]:
        import wtforms
        class Form(kwargs["Form"]):
            def __init__(self):
                super().__init__(prefix="manage_channel_form_")
            channel: wtforms.IntegerField = wtforms.IntegerField("Channel ID:", validators=[wtforms.validators.InputRequired(), kwargs["DpyObjectConverter"](discord.TextChannel)])
            submit: wtforms.SubmitField = wtforms.SubmitField("Set Channel")

        form: Form = Form()
        if form.validate_on_submit() and await form.validate_dpy_converters():
            channel = form.channel.data
            await self.config.guild(guild).application_channel.set(channel.id)
            return {
                "status": 0,
                "notifications": [{"message": f"The application channel has been set to {channel.mention}.", "category": "success"}],
                "redirect_url": kwargs["request_url"],
            }

        source = "{{ form|safe }}"

        return {
            "status": 0,
            "web_content": {"source": source, "form": form},
        }

    @dashboard_page(name="view_applications", description="View and manage applications.", methods=("GET", "POST"), is_owner=False)
    async def view_applications_page(self, user: discord.User, guild: discord.Guild, **kwargs) -> typing.Dict[str, typing.Any]:
        import wtforms
        class Form(kwargs["Form"]):
            def __init__(self):
                super().__init__(prefix="view_applications_form_")
            role: wtforms.IntegerField = wtforms.IntegerField("Role ID:", validators=[wtforms.validators.InputRequired(), kwargs["DpyObjectConverter"](discord.Role)])
            action: wtforms.SelectField = wtforms.SelectField("Action:", choices=[("accept", "Accept"), ("deny", "Deny")])
            user_id: wtforms.IntegerField = wtforms.IntegerField("User ID:", validators=[wtforms.validators.InputRequired()])
            submit: wtforms.SubmitField = wtforms.SubmitField("Update Application")

        form: Form = Form()
        if form.validate_on_submit() and await form.validate_dpy_converters():
            role = form.role.data
            action = form.action.data
            user_id = form.user_id.data
            member = guild.get_member(user_id)
            if not member:
                return {
                    "status": 0,
                    "notifications": [{"message": "Member not found.", "category": "error"}],
                    "redirect_url": kwargs["request_url"],
                }

            applications = await self.config.guild(guild).applications()
            if str(role.id) not in applications or str(user_id) not in applications[str(role.id)]:
                return {
                    "status": 0,
                    "notifications": [{"message": "Application not found.", "category": "error"}],
                    "redirect_url": kwargs["request_url"],
                }

            if action == "accept":
                await member.add_roles(role)
                auto_role_id = await self.config.guild(guild).auto_role()
                if auto_role_id:
                    auto_role = guild.get_role(auto_role_id)
                    if auto_role:
                        await member.add_roles(auto_role)
                await member.send(f"Congratulations! Your application for {role.mention} has been accepted.")
                embed = discord.Embed(title="Staff Hired", color=discord.Color.green())
                embed.add_field(name="Username", value=member.name, inline=False)
                embed.add_field(name="User ID", value=member.id, inline=False)
                embed.add_field(name="Position", value=role.mention, inline=False)
                embed.add_field(name="Issuer", value=user.name, inline=False)
                staff_updates_channel_id = await self.config.guild(guild).staff_updates_channel()
                staff_updates_channel = self.bot.get_channel(staff_updates_channel_id)
                if staff_updates_channel:
                    await staff_updates_channel.send(embed=embed)
                # Update the original application message
                message_id = applications[str(role.id)][str(user_id)].get("message_id")
                if message_id:
                    application_channel_id = await self.config.guild(guild).application_channel()
                    application_channel = self.bot.get_channel(application_channel_id)
                    message = await application_channel.fetch_message(message_id)
                    if message:
                        embed = message.embeds[0]
                        embed.set_field_at(-1, name="Status", value="Approved", inline=False)
                        await message.edit(embed=embed)
                return {
                    "status": 0,
                    "notifications": [{"message": f"Accepted {member.display_name} for {role.mention}.", "category": "success"}],
                    "redirect_url": kwargs["request_url"],
                }
            elif action == "deny":
                await member.send(f"Sorry, your application for role {role.mention} was denied.")
                # Update the original application message
                message_id = applications[str(role.id)][str(user_id)].get("message_id")
                if message_id:
                    application_channel_id = await self.config.guild(guild).application_channel()
                    application_channel = self.bot.get_channel(application_channel_id)
                    message = await application_channel.fetch_message(message_id)
                    if message:
                        embed = message.embeds[0]
                        embed.set_field_at(-1, name="Status", value="Denied", inline=False)
                        await message.edit(embed=embed)
                return {
                    "status": 0,
                    "notifications": [{"message": f"Denied {member.display_name}'s application for {role.mention}.", "category": "success"}],
                    "redirect_url": kwargs["request_url"],
                }

        applications = await self.config.guild(guild).applications()
        application_list = []
        for role_id, role_apps in applications.items():
            role = guild.get_role(int(role_id))
            for user_id, app in role_apps.items():
                member = guild.get_member(int(user_id))
                if member:
                    application_list.append(f"{member.display_name} ({member.id}) - {role.name}")

        source = f"<h4>Applications:</h4><ul>{''.join([f'<li>{app}</li>' for app in application_list])}</ul>{{{{ form|safe }}}}"

        return {
            "status": 0,
            "web_content": {"source": source, "form": form},
        }

    @dashboard_page(name="manage_staff", description="Manage staff members.", methods=("GET", "POST"), is_owner=False)
    async def manage_staff_page(self, user: discord.User, guild: discord.Guild, **kwargs) -> typing.Dict[str, typing.Any]:
        import wtforms
        class Form(kwargs["Form"]):
            def __init__(self):
                super().__init__(prefix="manage_staff_form_")
            member: wtforms.IntegerField = wtforms.IntegerField("Member ID:", validators=[wtforms.validators.InputRequired(), kwargs["DpyObjectConverter"](discord.Member)])
            action: wtforms.SelectField = wtforms.SelectField("Action:", choices=[("promote", "Promote"), ("demote", "Demote"), ("fire", "Fire")])
            role: wtforms.IntegerField = wtforms.IntegerField("Role ID:", validators=[wtforms.validators.Optional(), kwargs["DpyObjectConverter"](discord.Role)])
            submit: wtforms.SubmitField = wtforms.SubmitField("Update Staff")

        form: Form = Form()
        if form.validate_on_submit() and await form.validate_dpy_converters():
            member = form.member.data
            action = form.action.data
            role = form.role.data

            if action == "promote":
                await self.promote_member(guild, member, role, user)
                message = f"Promoted {member.display_name} to {role.name}."
                category = "success"
            elif action == "demote":
                await self.demote_member(guild, member, role, user)
                message = f"Demoted {member.display_name} to {role.name}."
                category = "success"
            elif action == "fire":
                await self.fire_member(guild, member, role, user)
                message = f"Fired {member.display_name} from {role.name}."
                category = "success"
            else:
                message = "Invalid action."
                category = "error"

            return {
                "status": 0,
                "notifications": [{"message": message, "category": category}],
                "redirect_url": kwargs["request_url"],
            }

        staff_list = []
        role_categories = await self.config.guild(guild).role_categories()
        for category, roles in role_categories.items():
            for role_id in roles:
                role = guild.get_role(int(role_id))
                if role:
                    for member in role.members:
                        staff_list.append(f"{member.display_name} ({member.id}) - {role.name}")

        source = f"<h4>Staff Members:</h4><ul>{''.join([f'<li>{staff}</li>' for staff in staff_list])}</ul>{{{{ form|safe }}}}"

        return {
            "status": 0,
            "web_content": {"source": source, "form": form},
        }

    async def promote_member(self, guild, member, new_role, issuer):
        role_categories = await self.config.guild(guild).role_categories()
        member_roles = [role for role in member.roles if role.id in [int(role_id) for roles in role_categories.values() for role_id in roles]]

        if not member_roles:
            return

        current_role = sorted(member_roles, key=lambda r: r.position, reverse=True)[0]
        category_name = next((cat for cat, roles in role_categories.items() if str(current_role.id) in roles), None)
        if not category_name:
            return

        roles_in_category = role_categories[category_name]
        current_index = roles_in_category.index(str(current_role.id))

        if new_role:
            if str(new_role.id) not in roles_in_category:
                return
        else:
            if current_index == len(roles_in_category) - 1:
                return
            new_role = guild.get_role(int(roles_in_category[current_index + 1]))

        await member.remove_roles(current_role)
        await member.add_roles(new_role)

        # Handle category role switch
        new_category_name = next((cat for cat, roles in role_categories.items() if str(new_role.id) in roles), None)
        if new_category_name and new_category_name != category_name:
            old_category_role = guild.get_role(int(role_categories[category_name][0]))
            new_category_role = guild.get_role(int(role_categories[new_category_name][0]))
            if old_category_role:
                await member.remove_roles(old_category_role)
            if new_category_role:
                await member.add_roles(new_category_role)

        embed = discord.Embed(title="Staff Promoted", color=discord.Color.blue())
        embed.add_field(name="Username", value=member.name, inline=False)
        embed.add_field(name="User ID", value=member.id, inline=False)
        embed.add_field(name="New Position", value=new_role.mention, inline=False)
        embed.add_field(name="Old Position", value=current_role.mention, inline=False)
        embed.add_field(name="Issuer", value=issuer.name, inline=False)
        staff_updates_channel_id = await self.config.guild(guild).staff_updates_channel()
        staff_updates_channel = self.bot.get_channel(staff_updates_channel_id)
        if staff_updates_channel:
            await staff_updates_channel.send(embed=embed)

    async def demote_member(self, guild, member, new_role, issuer):
        role_categories = await self.config.guild(guild).role_categories()
        member_roles = [role for role in member.roles if role.id in [int(role_id) for roles in role_categories.values() for role_id in roles]]

        if not member_roles:
            return

        current_role = sorted(member_roles, key=lambda r: r.position, reverse=True)[0]
        category_name = next((cat for cat, roles in role_categories.items() if str(current_role.id) in roles), None)
        if not category_name:
            return

        roles_in_category = role_categories[category_name]
        current_index = roles_in_category.index(str(current_role.id))

        if new_role:
            if str(new_role.id) not in roles_in_category:
                return
        else:
            if current_index == 0:
                return
            new_role = guild.get_role(int(roles_in_category[current_index - 1]))

        await member.remove_roles(current_role)
        await member.add_roles(new_role)

        # Handle category role switch
        new_category_name = next((cat for cat, roles in role_categories.items() if str(new_role.id) in roles), None)
        if new_category_name and new_category_name != category_name:
            old_category_role = guild.get_role(int(role_categories[category_name][0]))
            new_category_role = guild.get_role(int(role_categories[new_category_name][0]))
            if old_category_role:
                await member.remove_roles(old_category_role)
            if new_category_role:
                await member.add_roles(new_category_role)

        embed = discord.Embed(title="Staff Demoted", color=discord.Color.orange())
        embed.add_field(name="Username", value=member.name, inline=False)
        embed.add_field(name="User ID", value=member.id, inline=False)
        embed.add_field(name="New Position", value=new_role.mention, inline=False)
        embed.add_field(name="Old Position", value=current_role.mention, inline=False)
        embed.add_field(name="Issuer", value=issuer.name, inline=False)
        staff_updates_channel_id = await self.config.guild(guild).staff_updates_channel()
        staff_updates_channel = self.bot.get_channel(staff_updates_channel_id)
        if staff_updates_channel:
            await staff_updates_channel.send(embed=embed)

    async def fire_member(self, guild, member, role, issuer):
        await member.remove_roles(role)
        auto_role_id = await self.config.guild(guild).auto_role()
        if auto_role_id:
            auto_role = guild.get_role(auto_role_id)
            if auto_role:
                await member.remove_roles(auto_role)
        embed = discord.Embed(title="Staff Fired", color=discord.Color.red())
        embed.add_field(name="Username", value=member.name, inline=False)
        embed.add_field(name="User ID", value=member.id, inline=False)
        embed.add_field(name="Position", value=role.mention, inline=False)
        embed.add_field(name="Issuer", value=issuer.name, inline=False)
        staff_updates_channel_id = await self.config.guild(guild).staff_updates_channel()
        staff_updates_channel = self.bot.get_channel(staff_updates_channel_id)
        if staff_updates_channel:
            await staff_updates_channel.send(embed=embed)

    @dashboard_page(name="view_loa_requests", description="View and manage LOA requests.", methods=("GET", "POST"), is_owner=False)
    async def view_loa_requests_page(self, user: discord.User, guild: discord.Guild, **kwargs) -> typing.Dict[str, typing.Any]:
        import wtforms
        class Form(kwargs["Form"]):
            def __init__(self):
                super().__init__(prefix="view_loa_requests_form_")
            action: wtforms.SelectField = wtforms.SelectField("Action:", choices=[("accept", "Accept"), ("deny", "Deny")])
            user_id: wtforms.IntegerField = wtforms.IntegerField("User ID:", validators=[wtforms.validators.InputRequired()])
            submit: wtforms.SubmitField = wtforms.SubmitField("Update LOA Request")

        form: Form = Form()
        if form.validate_on_submit() and await form.validate_dpy_converters():
            action = form.action.data
            user_id = form.user_id.data

            loa_requests = await self.config.guild(guild).loa_requests()
            if str(user_id) not in loa_requests:
                return {
                    "status": 0,
                    "notifications": [{"message": "LOA request not found.", "category": "error"}],
                    "redirect_url": kwargs["request_url"],
                }

            loa_request = loa_requests[str(user_id)]
            user = guild.get_member(user_id)
            if not user:
                return {
                    "status": 0,
                    "notifications": [{"message": "User not found.", "category": "error"}],
                    "redirect_url": kwargs["request_url"],
                }

            if action == "accept":
                loa_request["approved_by"] = user.id
                loa_role_id = await self.config.guild(guild).loa_role()
                loa_role = guild.get_role(loa_role_id)
                if loa_role:
                    await user.add_roles(loa_role)
                embed = discord.Embed(title="Leave of Absence", color=discord.Color.green())
                embed.add_field(name="User", value=user.name, inline=False)
                embed.add_field(name="Duration", value=loa_request["duration"], inline=False)
                embed.add_field(name="Reason", value=loa_request["reason"], inline=False)
                embed.add_field(name="Approved by", value=user.name, inline=False)
                embed.add_field(name="Status", value="Approved", inline=False)
                staff_updates_channel_id = await self.config.guild(guild).staff_updates_channel()
                staff_updates_channel = self.bot.get_channel(staff_updates_channel_id)
                if staff_updates_channel:
                    await staff_updates_channel.send(embed=embed)
                message_id = loa_request.get("message_id")
                if message_id:
                    loa_requests_channel_id = await self.config.guild(guild).loa_requests_channel()
                    loa_requests_channel = self.bot.get_channel(loa_requests_channel_id)
                    message = await loa_requests_channel.fetch_message(message_id)
                    if message:
                        embed = message.embeds[0]
                        embed.set_field_at(-1, name="Status", value="Approved", inline=False)
                        await message.edit(embed=embed)
                return {
                    "status": 0,
                    "notifications": [{"message": f"Accepted LOA request for {user.name}.", "category": "success"}],
                    "redirect_url": kwargs["request_url"],
                }
            elif action == "deny":
                message_id = loa_request.get("message_id")
                if message_id:
                    loa_requests_channel_id = await self.config.guild(guild).loa_requests_channel()
                    loa_requests_channel = self.bot.get_channel(loa_requests_channel_id)
                    message = await loa_requests_channel.fetch_message(message_id)
                    if message:
                        embed = message.embeds[0]
                        embed.set_field_at(-1, name="Status", value="Denied", inline=False)
                        await message.edit(embed=embed)
                del loa_requests[str(user_id)]
                await self.config.guild(guild).loa_requests.set(loa_requests)
                return {
                    "status": 0,
                    "notifications": [{"message": f"Denied LOA request for {user.name}.", "category": "success"}],
                    "redirect_url": kwargs["request_url"],
                }

        loa_requests = await self.config.guild(guild).loa_requests()
        loa_list = []
        for user_id, loa_request in loa_requests.items():
            user = guild.get_member(int(user_id))
            if user:
                loa_list.append(f"{user.display_name} ({user.id}) - {loa_request['duration']} - {loa_request['reason']}")

        source = f"<h4>LOA Requests:</h4><ul>{''.join([f'<li>{loa}</li>' for loa in loa_list])}</ul>{{{{ form|safe }}}}"

        return {
            "status": 0,
            "web_content": {"source": source, "form": form},
        }

    @dashboard_page(name="view_resignation_requests", description="View and manage resignation requests.", methods=("GET", "POST"), is_owner=False)
    async def view_resignation_requests_page(self, user: discord.User, guild: discord.Guild, **kwargs) -> typing.Dict[str, typing.Any]:
        import wtforms
        class Form(kwargs["Form"]):
            def __init__(self):
                super().__init__(prefix="view_resignation_requests_form_")
            action: wtforms.SelectField = wtforms.SelectField("Action:", choices=[("accept", "Accept"), ("deny", "Deny")])
            user_id: wtforms.IntegerField = wtforms.IntegerField("User ID:", validators=[wtforms.validators.InputRequired()])
            submit: wtforms.SubmitField = wtforms.SubmitField("Update Resignation Request")

        form: Form = Form()
        if form.validate_on_submit() and await form.validate_dpy_converters():
            action = form.action.data
            user_id = form.user_id.data

            resignation_requests = await self.config.guild(guild).resignation_requests()
            if str(user_id) not in resignation_requests:
                return {
                    "status": 0,
                    "notifications": [{"message": "Resignation request not found.", "category": "error"}],
                    "redirect_url": kwargs["request_url"],
                }

            resignation_request = resignation_requests[str(user_id)]
            user = guild.get_member(user_id)
            if not user:
                return {
                    "status": 0,
                    "notifications": [{"message": "User not found.", "category": "error"}],
                    "redirect_url": kwargs["request_url"],
                }

            if action == "accept":
                resignation_request["approved_by"] = user.id
                embed = discord.Embed(title="Staff Member Resigned", color=discord.Color.red())
                embed.add_field(name="Former Staff", value=user.name, inline=False)
                embed.add_field(name="Reason", value=resignation_request["reason"], inline=False)
                embed.add_field(name="Approved by", value=user.name, inline=False)
                embed.add_field(name="Status", value="Approved", inline=False)
                staff_updates_channel_id = await self.config.guild(guild).staff_updates_channel()
                staff_updates_channel = self.bot.get_channel(staff_updates_channel_id)
                if staff_updates_channel:
                    await staff_updates_channel.send(embed=embed)
                message_id = resignation_request.get("message_id")
                if message_id:
                    resignation_requests_channel_id = await self.config.guild(guild).resignation_requests_channel()
                    resignation_requests_channel = self.bot.get_channel(resignation_requests_channel_id)
                    message = await resignation_requests_channel.fetch_message(message_id)
                    if message:
                        embed = message.embeds[0]
                        embed.set_field_at(-1, name="Status", value="Approved", inline=False)
                        await message.edit(embed=embed)
                return {
                    "status": 0,
                    "notifications": [{"message": f"Accepted resignation request for {user.name}.", "category": "success"}],
                    "redirect_url": kwargs["request_url"],
                }
            elif action == "deny":
                message_id = resignation_request.get("message_id")
                if message_id:
                    resignation_requests_channel_id = await self.config.guild(guild).resignation_requests_channel()
                    resignation_requests_channel = self.bot.get_channel(resignation_requests_channel_id)
                    message = await resignation_requests_channel.fetch_message(message_id)
                    if message:
                        embed = message.embeds[0]
                        embed.set_field_at(-1, name="Status", value="Denied", inline=False)
                        await message.edit(embed=embed)
                del resignation_requests[str(user_id)]
                await self.config.guild(guild).resignation_requests.set(resignation_requests)
                return {
                    "status": 0,
                    "notifications": [{"message": f"Denied resignation request for {user.name}.", "category": "success"}],
                    "redirect_url": kwargs["request_url"],
                }

        resignation_requests = await self.config.guild(guild).resignation_requests()
        resignation_list = []
        for user_id, resignation_request in resignation_requests.items():
            user = guild.get_member(int(user_id))
            if user:
                resignation_list.append(f"{user.display_name} ({user.id}) - {resignation_request['reason']}")

        source = f"<h4>Resignation Requests:</h4><ul>{''.join([f'<li>{resignation}</li>' for resignation in resignation_list])}</ul>{{{{ form|safe }}}}"

        return {
            "status": 0,
            "web_content": {"source": source, "form": form},
        }