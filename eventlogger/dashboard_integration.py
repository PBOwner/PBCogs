from redbot.core import commands
from redbot.core.bot import Red
import discord
import typing

def dashboard_page(*args, **kwargs):
    def decorator(func: typing.Callable):
        func.__dashboard_decorator_params__ = (args, kwargs)
        return func
    return decorator

class DashboardIntegration(commands.Cog):
    bot: Red

    @commands.Cog.listener()
    async def on_dashboard_cog_add(self, dashboard_cog: commands.Cog) -> None:
        dashboard_cog.rpc.third_parties_handler.add_third_party(self)

    @dashboard_page(name=None, description="Configure Event Logging", methods=("GET", "POST"), is_owner=True)
    async def configure_logging(self, user: discord.User, **kwargs) -> typing.Dict[str, typing.Any]:
        import wtforms
        class Form(kwargs["Form"]):
            def __init__(self):
                super().__init__(prefix="configure_logging_form_")
            event: wtforms.StringField = wtforms.StringField("Event:", validators=[wtforms.validators.InputRequired()])
            channel: wtforms.IntegerField = wtforms.IntegerField("Channel:", validators=[wtforms.validators.InputRequired(), kwargs["DpyObjectConverter"](discord.TextChannel)])
            submit: wtforms.SubmitField = wtforms.SubmitField("Set Logging Channel")

        form: Form = Form()
        if form.validate_on_submit() and await form.validate_dpy_converters():
            event = form.event.data
            channel = form.channel.data
            async with self.bot.get_cog("EventLogger").config.guild(kwargs["guild"]).channels() as channels:
                channels[event] = channel.id
            return {
                "status": 0,
                "notifications": [{"message": f"Logging channel for {event} set to {channel.mention}", "category": "success"}],
                "redirect_url": kwargs["request_url"],
            }

        source = "{{ form|safe }}"
        return {
            "status": 0,
            "web_content": {"source": source, "form": form},
        }
