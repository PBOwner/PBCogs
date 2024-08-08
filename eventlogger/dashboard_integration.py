import asyncio
import typing as t
from redbot.core import commands
from redbot.core.bot import Red
import discord
import wtforms

def dashboard_page(*args, **kwargs):
  def decorator(func: t.Callable):
    func.__dashboard_decorator_params__ = (args, kwargs)
    return func
  return decorator

class DashboardIntegration(commands.Cog):  # Inherit from commands.Cog
  bot: Red

  def __init__(self, bot: Red):
    self.bot = bot
    self._registered = False

  @commands.Cog.listener()
  async def on_dashboard_cog_add(self, dashboard_cog: commands.Cog) -> None:
    if not self._registered:
      try:
        dashboard_cog.rpc.third_parties_handler.add_third_party(self)
        self._registered = True
      except RuntimeError as e:
        # Log the error if needed
        print(f"Failed to register third party: {e}")

  async def get_logging_configuration(self, user: discord.User, guild: discord.Guild, **kwargs) -> t.Dict[str, t.Any]:
    channels = await self.bot.get_cog("EventLogger").config.guild(guild).channels()
    command_log_channel_id = await self.bot.get_cog("EventLogger").config.guild(guild).command_log_channel()
    command_log_channel = guild.get_channel(command_log_channel_id) if command_log_channel_id else None

    source = """
    <h3>Logging Configuration</h3>
    <form method="post" action="{{ request_url }}">
      <label for="event">Event:</label>
      <input type="text" id="event" name="event" required>

      <label for="channel">Channel:</label>
      <input type="number" id="channel" name="channel" required>

      <button type="submit">Set Logging Channel</button>
    </form>
    <h3>Current Configuration</h3>
    <ul>
      {% for event, channel_id in channels.items() %}
        <li>{{ event }}: {{ guild.get_channel(channel_id).mention if guild.get_channel(channel_id) else "Unknown Channel" }}</li>
      {% endfor %}
      {% if command_log_channel %}
        <li>Command Log: {{ command_log_channel.mention }}</li>
      {% endif %}
    </ul>
    """

    return {
      "status": 0,
      "web_content": {
        "source": source,
        "channels": channels,
        "command_log_channel": command_log_channel,
        "guild": guild,
        "request_url": kwargs["request_url"],
      },
    }

  @dashboard_page(name="configure", description="Configure Event Logging", methods=("GET", "POST"), is_owner=True)
  async def configure_logging_page(self, user: discord.User, guild: discord.Guild, **kwargs) -> t.Dict[str, t.Any]:
    if kwargs["method"] == "POST":
      form = kwargs["data"]["form"]
      event = form.get("event")
      channel_id = int(form.get("channel"))
      async with self.bot.get_cog("EventLogger").config.guild(guild).channels() as channels:
        channels[event] = channel_id
      return {
        "status": 0,
        "notifications": [{"message": f"Logging channel for {event} set to <#{channel_id}>", "category": "success"}],
        "redirect_url": kwargs["request_url"],
      }
    return await self.get_logging_configuration(user, guild, **kwargs)
