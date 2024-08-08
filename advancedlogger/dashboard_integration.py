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

    @dashboard_page(name="log_settings", description="Manage log settings for the server.", methods=("GET", "POST"), is_owner=True)
    async def log_settings_page(self, user: discord.User, guild: discord.Guild, **kwargs) -> typing.Dict[str, typing.Any]:
        import wtforms
        class Form(kwargs["Form"]):
            def __init__(self):
                super().__init__(prefix="log_settings_form_")
            log_type: wtforms.SelectField = wtforms.SelectField("Log Type:", choices=[
                ("member", "Member"),
                ("role", "Role"),
                ("role_permissions", "Role Permissions"),
                ("message", "Message"),
                ("channel", "Channel"),
                ("channel_permissions", "Channel Permissions"),
                ("webhook", "Webhook"),
                ("app", "App"),
                ("voice", "Voice"),
                ("reaction", "Reaction"),
                ("emoji", "Emoji"),
                ("kick", "Kick"),
                ("ban", "Ban"),
                ("mute", "Mute"),
                ("timeout", "Timeout"),
                ("attachment", "Attachment"),
                ("link", "Link"),
                ("slash", "Slash"),
                ("guild", "Guild"),
                ("invite", "Invite"),
                ("integration", "Integration"),
                ("typing", "Typing"),
                ("thread", "Thread"),
                ("sticker", "Sticker"),
                ("scheduled_event", "Scheduled Event"),
                ("stage_instance", "Stage Instance"),
                ("command", "Command")
            ])
            channel: wtforms.IntegerField = wtforms.IntegerField("Channel ID:", validators=[wtforms.validators.InputRequired(), kwargs["DpyObjectConverter"](discord.TextChannel)])
            submit: wtforms.SubmitField = wtforms.SubmitField("Update Log Settings")

        form: Form = Form()
        if form.validate_on_submit() and await form.validate_dpy_converters():
            log_type = form.log_type.data
            channel = form.channel.data
            await self.config.guild(guild).set_raw(log_type + "_log_channel", value=channel.id)
            return {
                "status": 0,
                "notifications": [{"message": f"{log_type.capitalize()} logging channel set to {channel.mention}", "category": "success"}],
                "redirect_url": kwargs["request_url"],
            }

        source = "{{ form|safe }}"

        return {
            "status": 0,
            "web_content": {"source": source, "form": form},
        }
