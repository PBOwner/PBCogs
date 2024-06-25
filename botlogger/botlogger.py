import discord
from discord.ext import tasks
from redbot.core import commands, Config
from redbot.core.bot import Red
import logging

logger = logging.getLogger("red.botlogger")

class BotLogger(commands.Cog):
    """A cog to log bot installations to servers and user profiles."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567893)
        self.config.register_global(log_channel=None)
        self.config.register_user(installed=False)
        self.config.register_guild(installed=False)

        # Set up logging to a file
        handler = logging.FileHandler(filename='bot_install.log', encoding='utf-8', mode='a')
        handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        self.check_user_installs.start()

    def cog_unload(self):
        self.check_user_installs.cancel()

    @commands.group()
    @commands.is_owner()
    async def botlog(self, ctx):
        """Group of commands to configure bot logging."""
        pass

    @botlog.command()
    async def setlogchannel(self, ctx, channel: discord.TextChannel):
        """Set the channel where logs will be sent."""
        await self.config.log_channel.set(channel.id)
        await ctx.send(f"Log channel set to {channel.mention}")

    @botlog.command()
    async def usercount(self, ctx):
        """Get the total count of users who have installed the bot to their profile."""
        all_users = await self.config.all_users()
        installed_users = [user_id for user_id, data in all_users.items() if data['installed']]
        total_installed_users = len(installed_users)
        await ctx.send(f"The total number of users who have installed the bot to their profile is: {total_installed_users}")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Event when the bot is added to a server."""
        await self.config.guild(guild).installed.set(True)
        log_message = f"Bot added to server: {guild.name} (ID: {guild.id})"
        logger.info(log_message)
        await self.send_log(log_message, guild)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        """Event when the bot is removed from a server."""
        await self.config.guild(guild).installed.set(False)
        log_message = f"Bot removed from server: {guild.name} (ID: {guild.id})"
        logger.info(log_message)
        await self.send_log(log_message, guild)

    @tasks.loop(minutes=5)
    async def check_user_installs(self):
        """Periodically check user installations."""
        all_users = await self.config.all_users()
        for user_id, data in all_users.items():
            if data['installed']:
                user = self.bot.get_user(user_id)
                if user:
                    log_message = f"Bot installed to user profile: {user.name} (ID: {user.id})"
                    logger.info(log_message)
                    await self.send_log(log_message, user=user)

    async def send_log(self, message, guild=None, user=None):
        """Send log message to the configured log channel as an embed."""
        log_channel_id = await self.config.log_channel()
        if log_channel_id:
            log_channel = self.bot.get_channel(log_channel_id)
            if log_channel:
                embed = discord.Embed(title="Bot Installation Log", description=message, color=discord.Color.blue())
                if guild:
                    embed.add_field(name="Server Name", value=guild.name, inline=True)
                    embed.add_field(name="Server ID", value=guild.id, inline=True)
                if user:
                    embed.add_field(name="User Name", value=user.name, inline=True)
                    embed.add_field(name="User ID", value=user.id, inline=True)
                await log_channel.send(embed=embed)

def setup(bot: Red):
    bot.add_cog(BotLogger(bot))
