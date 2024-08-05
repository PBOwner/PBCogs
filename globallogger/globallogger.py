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

    async def log_global_event(self, log_type: str, title: str, description: str, color: discord.Color = discord.Color.blue(), author: discord.Member = None):
        try:
            log_channel_id = await self.config.get_raw(log_type + "_log_channel")
            if log_channel_id:
                log_channel = self.bot.get_channel(log_channel_id)
                if log_channel:
                    embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.utcnow())
                    if author:
                        embed.set_thumbnail(url=author.display_avatar.url)
                    await log_channel.send(embed=embed)
                else:
                    print(f"Log channel not found for log type: {log_type}")
            else:
                print(f"No log channel set for log type: {log_type}")
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
        if log_type not in valid_log_types:
            await ctx.send(f"Invalid log type. Valid log types are: {', '.join(valid_log_types)}")
            return
        await self.config.set_raw(log_type + "_log_channel", value=None)
        await ctx.send(f"{log_type.capitalize()} logging channel removed")

    @commands.Cog.listener()
    async def on_command(self, ctx):
        log_channel_id = await self.config.get_raw("command_log_channel")
        if ctx.guild and ctx.guild.id == self.bot.get_channel(log_channel_id).guild.id:
            return

        channel_info = f"{ctx.channel.name} ({ctx.channel.mention})" if isinstance(ctx.channel, discord.TextChannel) else f"Direct Message ({ctx.channel.id})"
        guild_info = f"{ctx.guild.name} ({ctx.guild.id})" if ctx.guild else "Direct Message"

        description = (
            f"**Command Ran:** {ctx.command}\n"
            f"**Ran By:** {ctx.author} ({ctx.author.mention})\n"
            f"**User ID:** {ctx.author.id}\n"
            f"**Where:** {channel_info}\n"
            f"**Channel ID:** {ctx.channel.id}\n"
            f"**Guild:** {guild_info}\n"
            f"**Timestamp:** {ctx.message.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            f"**Message Content:** {ctx.message.content}"
        )
        await self.log_global_event("command", "Command Executed", description, discord.Color.purple(), ctx.author)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        log_channel_id = await self.config.get_raw("error_log_channel")
        if ctx.guild and ctx.guild.id == self.bot.get_channel(log_channel_id).guild.id:
            return

        channel_info = f"{ctx.channel.name} ({ctx.channel.mention})" if isinstance(ctx.channel, discord.TextChannel) else f"Direct Message ({ctx.channel.id})"
        guild_info = f"{ctx.guild.name} ({ctx.guild.id})" if ctx.guild else "Direct Message"

        tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        description = (
            f"**Command Ran:** {ctx.command}\n"
            f"**Ran By:** {ctx.author} ({ctx.author.mention})\n"
            f"**User ID:** {ctx.author.id}\n"
            f"**Where:** {channel_info}\n"
            f"**Channel ID:** {ctx.channel.id}\n"
            f"**Guild:** {guild_info}\n"
            f"**Timestamp:** {ctx.message.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            f"**Message Content:** {ctx.message.content}\n"
            f"**Error Type:** {type(error).__name__}\n"
            f"**Error Message:** {str(error)}\n"
            f"**Stack Trace:** ```python\n{tb}```"
        )
        await self.log_global_event("error", "Command Error", description, discord.Color.red(), ctx.author)
