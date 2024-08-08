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

    @dashboard_page(name="manage_roles", description="Manage the roles for the Chain of Command.", methods=("GET", "POST"), is_owner=True)
    async def manage_roles_page(self, user: discord.User, guild: discord.Guild, **kwargs) -> typing.Dict[str, typing.Any]:
        import wtforms
        class Form(kwargs["Form"]):
            def __init__(self):
                super().__init__(prefix="manage_roles_form_")
            role: wtforms.IntegerField = wtforms.IntegerField("Role ID:", validators=[wtforms.validators.InputRequired(), kwargs["DpyObjectConverter"](discord.Role)])
            action: wtforms.SelectField = wtforms.SelectField("Action:", choices=[("add", "Add"), ("remove", "Remove")])
            submit: wtforms.SubmitField = wtforms.SubmitField("Update Roles")

        form: Form = Form()
        if form.validate_on_submit() and await form.validate_dpy_converters():
            role = form.role.data
            action = form.action.data
            async with self.config.guild(guild).roles() as roles:
                if action == "add":
                    if role.id not in roles:
                        roles.append(role.id)
                        message = f"Role `{role.name}` has been added to the list."
                        category = "success"
                    else:
                        message = f"Role `{role.name}` is already in the list."
                        category = "warning"
                elif action == "remove":
                    if role.id in roles:
                        roles.remove(role.id)
                        message = f"Role `{role.name}` has been removed from the list."
                        category = "success"
                    else:
                        message = f"Role `{role.name}` is not in the list."
                        category = "warning"
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

    @dashboard_page(name="manage_channel", description="Set the channel for Chain of Command updates.", methods=("GET", "POST"), is_owner=True)
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
            await self.config.guild(guild).channel_id.set(channel.id)
            return {
                "status": 0,
                "notifications": [{"message": f"The channel `{channel.name}` has been set for Chain of Command updates.", "category": "success"}],
                "redirect_url": kwargs["request_url"],
            }

        source = "{{ form|safe }}"

        return {
            "status": 0,
            "web_content": {"source": source, "form": form},
        }
