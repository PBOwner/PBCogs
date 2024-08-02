import logging
import asyncio
import subprocess
from datetime import datetime
from typing import Optional

import discord
from discord.ext import tasks
from redbot.core import commands, Config
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_number

log = logging.getLogger("red.dynamic_shard_manager")

class DynamicShardManager(commands.Cog):
    """A cog to manage shards dynamically and handle rate limits."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        default_guild = {
            "logging_channel": None,
        }
        default_global = {
            "shard_count": len(self.bot.shards),
            "restart_message": "Restarting the bot to add more shards",
            "logging_guild_id": None
        }
        self.config.register_guild(**default_guild)
        self.config.register_global(**default_global)
        self.monitor_shards.start()

    def cog_unload(self):
        self.monitor_shards.cancel()

    @tasks.loop(minutes=1)
    async def monitor_shards(self):
        """Monitor the shards and handle rate limiting."""
        try:
            await self.handle_shards()
        except Exception as e:
            log.exception("An error occurred while monitoring shards: %s", e)

    async def handle_shards(self):
        """Handle shard management and rate limiting."""
        shard_count = len(self.bot.shards)
        log.info(f"Monitoring {shard_count} shards.")

        for shard_id, shard in self.bot.shards.items():
            if shard.is_closed():
                log.warning(f"Shard {shard_id} is closed. Restarting...")
                await self.bot.launch_shard(shard_id)

        # Check for high latency as a proxy for rate limiting issues
        high_latency_shards = [shard for shard in self.bot.shards.values() if shard.latency > 1.0]
        if high_latency_shards:
            log.warning("High latency detected. Adjusting shard count...")
            await self.add_shard()

        await self.update_logging_channel()

    async def add_shard(self):
        """Add a new shard to handle rate limiting."""
        current_shard_count = await self.config.shard_count()
        new_shard_count = current_shard_count + 1
        log.info(f"Increasing shard count to {new_shard_count}.")

        await self.config.shard_count.set(new_shard_count)
        await self.distribute_guilds_evenly(new_shard_count)
        await self.restart_bot()

    async def restart_bot(self):
        """Restart the bot using the Termino method."""
        log.info("Restarting the bot to apply new shard count...")
        message = await self.config.restart_message()
        await self.update_bot()
        await self.bot.shutdown(restart=True)

    async def update_bot(self):
        """Update the bot from the specified GitHub repository."""
        log.info("Updating the bot from the GitHub repository...")
        result = subprocess.run(["pip", "install", "--upgrade", "git+https://github.com/PBOwner/DevBot"], capture_output=True, text=True)
        if result.returncode == 0:
            log.info("Bot updated successfully.")
        else:
            log.error(f"Failed to update the bot: {result.stderr}")

    async def distribute_guilds_evenly(self, shard_count: int):
        """Distribute guilds evenly across all shards."""
        guilds = list(self.bot.guilds)
        guilds.sort(key=lambda g: g.id)
        for i, guild in enumerate(guilds):
            shard_id = i % shard_count
            await self.bot.change_presence(shard_id=shard_id, guild=guild)
        log.info("Distributed guilds evenly across all shards.")

    async def update_logging_channel(self):
        """Update the logging channel with shard information."""
        global_data = await self.config.all_global()
        guild_id = global_data.get("logging_guild_id")
        if not guild_id:
            log.error("Guild ID is not set.")
            return

        guild = self.bot.get_guild(guild_id)
        if not guild:
            log.error(f"Guild with ID {guild_id} not found.")
            return

        channel_id = await self.config.guild(guild).logging_channel()
        if not channel_id:
            log.error("Logging channel is not set.")
            return

        channel = guild.get_channel(channel_id)
        if not channel:
            log.error(f"Channel with ID {channel_id} not found.")
            return

        embed = discord.Embed(
            title="Shard Manager Status",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )

        embed.add_field(name="Shard Count", value=humanize_number(len(self.bot.shards)))

        for shard_id, shard in self.bot.shards.items():
            shard_info = (
                f"Status: {'Closed' if shard.is_closed() else 'Open'}\n"
                f"Latency: {shard.latency * 1000:.2f} ms\n"
                f"Guilds: {len([g for g in self.bot.guilds if g.shard_id == shard_id])}\n"
                f"Users: {len([u for u in self.bot.users if u.mutual_guilds and any(g.shard_id == shard_id for g in u.mutual_guilds)])}\n"
                f"Channels: {len([c for c in self.bot.get_all_channels() if c.guild and c.guild.shard_id == shard_id])}\n"
            )
            embed.add_field(
                name=f"Shard {shard_id}",
                value=shard_info,
                inline=False
            )

        async for message in channel.history(limit=10):
            if message.author == self.bot.user and message.embeds:
                await message.edit(embed=embed)
                break
        else:
            await channel.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def setlogchannel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the logging channel for shard updates."""
        await self.config.guild(ctx.guild).logging_channel.set(channel.id)
        await self.config.logging_guild_id.set(ctx.guild.id)
        await ctx.send(f"Logging channel set to {channel.mention}.")

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def addshard(self, ctx: commands.Context):
        """Manually add a new shard."""
        await self.add_shard()
        await ctx.send("Shard count increased. Restarting bot to apply changes...")

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def sendstatus(self, ctx: commands.Context):
        """Send the dynamic shard status embed to the logging channel."""
        await self.update_logging_channel()
        await ctx.send("Shard status embed sent to the logging channel.")
