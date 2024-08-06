import discord
import asyncio
from redbot.core import commands, Config
from redbot.core.bot import Red
from datetime import datetime, timedelta

class AutoConfigCleaner(commands.Cog):
    """Automatically deletes server configurations 15 minutes after the bot leaves the server."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567892)
        self.config.register_guild(deletion_scheduled=False, log_message_id=None)
        self.config.register_global(log_channel=None)
        self.bot.loop.create_task(self.purge_stale_configs())

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        """Event listener for when the bot leaves a server."""
        await self.schedule_deletion(guild)

    async def schedule_deletion(self, guild: discord.Guild):
        """Schedules the deletion of the server's configurations after 15 minutes."""
        await self.config.guild(guild).deletion_scheduled.set(True)
        purge_time = datetime.utcnow() + timedelta(minutes=15)
        log_message = await self.log_deletion_notice(guild, purge_time)
        await self.config.guild(guild).log_message_id.set(log_message.id)
        await asyncio.sleep(900)  # 15 minutes in seconds

        # Check if the deletion is still scheduled
        if await self.config.guild(guild).deletion_scheduled():
            await self.config.clear_all_guilds()  # Delete all configurations for the guild
            await self.config.guild(guild).deletion_scheduled.set(False)
            await self.edit_log_deletion(guild, log_message)
            await self.config.guild(guild).log_message_id.set(None)

    @commands.command()
    @commands.is_owner()
    async def canceldeletion(self, ctx: commands.Context, guild_id: int):
        """Cancels the scheduled deletion for a specific guild."""
        guild = self.bot.get_guild(guild_id)
        if guild:
            await self.config.guild(guild).deletion_scheduled.set(False)
            await ctx.send(f"Canceled scheduled deletion for guild: {guild.name} ({guild.id})")
            await self.log(f"Canceled scheduled deletion for guild: {guild.name} ({guild.id})")
        else:
            await ctx.send(f"No guild found with ID: {guild_id}")

    @commands.command()
    @commands.is_owner()
    async def setdellog(self, ctx: commands.Context, channel: discord.TextChannel):
        """Sets the log channel for purge notifications."""
        await self.config.log_channel.set(channel.id)
        await ctx.send(f"Log channel set to {channel.mention}")

    async def purge_stale_configs(self):
        """Purges configurations for guilds that the bot is not currently in."""
        await self.bot.wait_until_ready()
        all_guild_ids = set(guild.id for guild in self.bot.guilds)
        async with self.config.all_guilds() as all_guilds:
            stale_guild_ids = [guild_id for guild_id in all_guilds if guild_id not in all_guild_ids]
            for guild_id in stale_guild_ids:
                await self.config.guild_from_id(guild_id).clear()
                await self.log(f"Purged stale configuration for guild ID: {guild_id}")

    async def log_deletion_notice(self, guild: discord.Guild, purge_time: datetime):
        """Logs a deletion notice to the configured log channel."""
        log_channel_id = await self.config.log_channel()
        if log_channel_id:
            log_channel = self.bot.get_channel(log_channel_id)
            if log_channel:
                embed = discord.Embed(
                    title="Server Config Deletion Notice",
                    color=discord.Color.orange(),
                    timestamp=purge_time
                )
                embed.add_field(name="Server Name", value=guild.name, inline=False)
                embed.add_field(name="Server ID", value=guild.id, inline=False)
                embed.add_field(name="Server Owner", value=guild.owner, inline=False)
                embed.add_field(name="Time Until Deletion", value=f"<t:{int(purge_time.timestamp())}:R>", inline=False)
                return await log_channel.send(embed=embed)

    async def edit_log_deletion(self, guild: discord.Guild, log_message):
        """Edits the log message to indicate that the server configurations have been deleted."""
        log_channel_id = await self.config.log_channel()
        if log_channel_id:
            log_channel = self.bot.get_channel(log_channel_id)
            if log_channel:
                embed = discord.Embed(
                    title="Server Config Deleted",
                    color=discord.Color.red(),
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="Server Name", value=guild.name, inline=False)
                embed.add_field(name="Server ID", value=guild.id, inline=False)
                embed.add_field(name="Server Owner", value=guild.owner, inline=False)
                embed.add_field(name="Time Deleted", value=f"<t:{int(datetime.utcnow().timestamp())}>", inline=False)
                await log_message.edit(embed=embed)

    async def log(self, message: str):
        """Logs a message to the configured log channel."""
        log_channel_id = await self.config.log_channel()
        if log_channel_id:
            log_channel = self.bot.get_channel(log_channel_id)
            if log_channel:
                embed = discord.Embed(description=message, color=discord.Color.blue())
                await log_channel.send(embed=embed)
