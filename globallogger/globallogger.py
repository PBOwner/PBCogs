import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
from datetime import datetime
import traceback

class GlobalLogger(commands.Cog):
    """A cog for global logging of commands and errors"""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=9876543210)
        default_global = {
            "command_log_channel": None,
            "error_log_channel": None,
        }
        self.config.register_global(**default_global)

    async def log_global_event(self, log_type: str, title: str, fields: dict, color: discord.Color = discord.Color.blue(), author: discord.Member = None):
        try:
            log_channel_id = await self.config.get_raw(log_type + "_log_channel")
            if log_channel_id:
                log_channel = self.bot.get_channel(log_channel_id)
                if log_channel:
                    embed = discord.Embed(title=title, color=color, timestamp=datetime.utcnow())
                    for name, value in fields.items():
                        embed.add_field(name=name, value=value, inline=False)
                    if author:
                        embed.set_thumbnail(url=author.display_avatar.url)
                    await log_channel.send(embed=embed)
        except Exception as e:
            print(f"Failed to log global event: {e}")

    @commands.group()
    @commands.is_owner()
    async def globallogging(self, ctx):
        """Manage global logging settings for commands and errors."""
        pass

    @globallogging.command()
    async def setglobalchannel(self, ctx, log_type: str, channel: discord.TextChannel):
        """Set the global channel for logging commands and errors.

        **Valid log types**: command, error

        **Example**:
        `[p]globallogging setglobalchannel command #command-log`
        `[p]globallogging setglobalchannel error #error-log`
        """
        valid_log_types = ["command", "error"]
        if log_type not in valid_log_types:
            await ctx.send(f"Invalid log type. Valid log types are: {', '.join(valid_log_types)}")
            return
        await self.config.set_raw(log_type + "_log_channel", value=channel.id)
        await ctx.send(f"{log_type.capitalize()} logging channel set to {channel.mention}")

    @globallogging.command()
    async def removeglobalchannel(self, ctx, log_type: str):
        """Remove the global logging channel for commands and errors.

        **Valid log types**: command, error

        **Example**:
        `[p]globallogging removeglobalchannel command`
        `[p]globallogging removeglobalchannel error`
        """
        valid_log_types = ["command", "error"]
        if log_type not in valid log_types:
            await ctx.send(f"Invalid log type. Valid log types are: {', '.join(valid log_types)}")
            return
        await self.config.set_raw(log_type + "_log_channel", value=None)
        await ctx.send(f"{log_type.capitalize()} logging channel removed")

    @commands.Cog.listener()
    async def on_command(self, ctx):
        fields = {
            "Command Ran": ctx.command,
            "Ran By": ctx.author.mention,
            "Where": ctx.channel.mention,
        }
        await self.log_global_event("command", "Command Executed", fields, discord.Color.purple(), ctx.author)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        fields = {
            "Command Ran": ctx.command,
            "Ran By": ctx.author.mention,
            "Error": f"```python\n{tb}```",
            "Where": ctx.channel.mention,
        }
        await self.log_global_event("error", "Command Error", fields, discord.Color.red(), ctx.author)
