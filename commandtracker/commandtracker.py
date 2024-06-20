import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
from collections import Counter
from datetime import datetime, timezone

class CommandTracker(commands.Cog):
    """A cog to track and display popular commands and total command count."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_global(command_count=0, command_usage={})
        self.command_counter = Counter()

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context):
        """Track command usage."""
        command_name = ctx.command.qualified_name
        self.command_counter[command_name] += 1
        await self.config.command_count.set(self.config.command_count() + 1)
        async with self.config.command_usage() as command_usage:
            command_usage[command_name] = self.command_counter[command_name]
        await self.update_command_list_embed(ctx.guild)

    async def update_command_list_embed(self, guild: discord.Guild):
        """Update the command usage embed in the specified channel."""
        command_list_channel_id = await self.config.guild(guild).command_list_channel()
        embed_message_id = await self.config.guild(guild).embed_message_id()
        command_list_channel = guild.get_channel(command_list_channel_id) if command_list_channel_id else None

        if not command_list_channel:
            return

        command_usage = await self.config.command_usage()
        command_count = await self.config.command_count()
        total_commands = len(self.bot.commands)

        sorted_commands = sorted(command_usage.items(), key=lambda x: x[1], reverse=True)
        popular_commands = "\n".join([f"{cmd}: {count}" for cmd, count in sorted_commands[:10]])

        embed = discord.Embed(
            title="Popular Commands",
            color=discord.Color.blue(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="Total Commands Executed", value=command_count, inline=False)
        embed.add_field(name="Total Commands Available", value=total_commands, inline=False)
        embed.add_field(name="Top 10 Commands", value=popular_commands if popular_commands else "None", inline=False)

        if embed_message_id:
            try:
                message = await command_list_channel.fetch_message(embed_message_id)
                await message.edit(embed=embed)
            except discord.NotFound:
                message = await command_list_channel.send(embed=embed)
                await self.config.guild(guild).embed_message_id.set(message.id)
        else:
            message = await command_list_channel.send(embed=embed)
            await self.config.guild(guild).embed_message_id.set(message.id)

    @commands.group(name="commandtracker", aliases=["ct"])
    @commands.guild_only()
    @commands.admin()
    async def commandtracker(self, ctx: commands.Context):
        """Group command for managing command tracking settings."""
        pass

    @commandtracker.command()
    async def setchannel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the channel for displaying the command usage embed."""
        await self.config.guild(ctx.guild).command_list_channel.set(channel.id)
        embed = discord.Embed(
            title="Command List Channel Set",
            description=f"Command usage will be displayed in {channel.mention}.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        await self.update_command_list_embed(ctx.guild)

    @commandtracker.command()
    async def status(self, ctx: commands.Context):
        """Check the current settings for command tracking."""
        guild = ctx.guild
        command_list_channel_id = await self.config.guild(guild).command_list_channel()
        command_list_channel = guild.get_channel(command_list_channel_id) if command_list_channel_id else "Not set"

        embed = discord.Embed(
            title="Command Tracking Settings",
            color=discord.Color.blue()
        )
        embed.add_field(name="Command List Channel", value=command_list_channel, inline=False)

        await ctx.send(embed=embed)

def setup(bot: Red):
    bot.add_cog(CommandTracker(bot))
