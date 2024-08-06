import discord
import asyncio
from redbot.core import commands, Config
from redbot.core.bot import Red

class AutoConfigCleaner(commands.Cog):
    """Automatically deletes server configurations 15 minutes after the bot leaves the server."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567892)
        self.config.register_guild(deletion_scheduled=False)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        """Event listener for when the bot leaves a server."""
        await self.schedule_deletion(guild)

    async def schedule_deletion(self, guild: discord.Guild):
        """Schedules the deletion of the server's configurations after 15 minutes."""
        await self.config.guild(guild).deletion_scheduled.set(True)
        await asyncio.sleep(900)  # 15 minutes in seconds

        # Check if the deletion is still scheduled
        if await self.config.guild(guild).deletion_scheduled():
            await self.config.clear_all_guilds()  # Delete all configurations for the guild
            await self.config.guild(guild).deletion_scheduled.set(False)
            print(f"Deleted configurations for guild: {guild.name} ({guild.id})")

    @commands.command()
    @commands.is_owner()
    async def canceldeletion(self, ctx: commands.Context, guild_id: int):
        """Cancels the scheduled deletion for a specific guild."""
        guild = self.bot.get_guild(guild_id)
        if guild:
            await self.config.guild(guild).deletion_scheduled.set(False)
            await ctx.send(f"Canceled scheduled deletion for guild: {guild.name} ({guild.id})")
        else:
            await ctx.send(f"No guild found with ID: {guild_id}")
