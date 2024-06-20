import discord
from redbot.core import commands, Config
from redbot.core.bot import Red

class PresenceTracker(commands.Cog):
    """Cog to track user presence updates with detailed activity logging and management."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567895, force_registration=True)
        default_guild = {
            "log_channel": None,
            "tracked_games": [],
            "ignored_users": []
        }
        self.config.register_guild(**default_guild)

    @commands.group(aliases=["pt"])
    async def presence(self, ctx: commands.Context):
        """Base command for presence tracking."""
        pass

    @presence.command()
    @commands.has_permissions(manage_guild=True)
    async def setlogchannel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the channel where presence updates will be logged."""
        await self.config.guild(ctx.guild).log_channel.set(channel.id)
        await ctx.send(f"Log channel set to {channel.mention}")

    @presence.command()
    @commands.has_permissions(manage_guild=True)
    async def addgame(self, ctx: commands.Context, *, game_name: str):
        """Add a game to the tracking list."""
        async with self.config.guild(ctx.guild).tracked_games() as tracked_games:
            if game_name not in tracked_games:
                tracked_games.append(game_name)
                await ctx.send(f"Game '{game_name}' added to the tracking list.")
            else:
                await ctx.send(f"Game '{game_name}' is already being tracked.")

    @presence.command()
    @commands.has_permissions(manage_guild=True)
    async def removegame(self, ctx: commands.Context, *, game_name: str):
        """Remove a game from the tracking list."""
        async with self.config.guild(ctx.guild).tracked_games() as tracked_games:
            if game_name in tracked_games:
                tracked_games.remove(game_name)
                await ctx.send(f"Game '{game_name}' removed from the tracking list.")
            else:
                await ctx.send(f"Game '{game_name}' is not being tracked.")

    @presence.command()
    async def ignore(self, ctx: commands.Context):
        """Opt-out from being tracked."""
        async with self.config.guild(ctx.guild).ignored_users() as ignored_users:
            if ctx.author.id in ignored_users:
                ignored_users.remove(ctx.author.id)
                await ctx.send("You have been removed from the tracking ignore list.")
            else:
                ignored_users.append(ctx.author.id)
                await ctx.send("You have been added to the tracking ignore list.")

    @presence.command()
    async def mystatus(self, ctx: commands.Context):
        """Check your current status and activities."""
        member = ctx.author
        await self.send_status_embed(ctx, member)

    @presence.command()
    async def userstatus(self, ctx: commands.Context, member: discord.Member):
        """Check the status and activities of another user."""
        await self.send_status_embed(ctx, member)

    @presence.command()
    async def listgames(self, ctx: commands.Context):
        """List all currently tracked games."""
        tracked_games = await self.config.guild(ctx.guild).tracked_games()
        if not tracked_games:
            await ctx.send("No games are currently being tracked.")
        else:
            await ctx.send(f"Currently tracked games: {', '.join(tracked_games)}")

    async def send_status_embed(self, ctx: commands.Context, member: discord.Member):
        embed = discord.Embed(
            title=f"{member.display_name}'s Status",
            description=f"Status: {str(member.status).capitalize()}",
            color=discord.Color.blue()
        )
        if member.activities:
            activities = []
            for activity in member.activities:
                if isinstance(activity, discord.Game):
                    activities.append(f"Playing: {activity.name}")
                elif isinstance(activity, discord.Streaming):
                    activities.append(f"Streaming: {activity.name} (URL: {activity.url})")
                elif isinstance(activity, discord.Spotify):
                    activities.append(f"Listening to: {activity.title} by {', '.join(activity.artists)}")
                elif isinstance(activity, discord.Activity):
                    activities.append(f"Activity: {activity.name}")
            embed.add_field(name="Activities", value="\n".join(activities), inline=False)
        else:
            embed.add_field(name="Activities", value="No current activities", inline=False)
        embed.set_footer(text=f"User ID: {member.id}")
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        log_channel_id = await self.config.guild(after.guild).log_channel()
        if not log_channel_id:
            return

        log_channel = after.guild.get_channel(log_channel_id)
        if not log_channel:
            return

        ignored_users = await self.config.guild(after.guild).ignored_users()
        if after.id in ignored_users:
            return

        if before.status != after.status:
            embed = discord.Embed(
                title="Presence Update",
                description=f"{after.mention} has changed their status.",
                color=discord.Color.blue()
            )
            embed.add_field(name="Before", value=str(before.status).capitalize(), inline=True)
            embed.add_field(name="After", value=str(after.status).capitalize(), inline=True)
            embed.set_footer(text=f"User ID: {after.id}")
            await log_channel.send(embed=embed)

        if before.activities != after.activities:
            await self.log_activity_update(before, after, log_channel)

    async def log_activity_update(self, before: discord.Member, after: discord.Member, log_channel: discord.TextChannel):
        before_activities = {type(activity): activity for activity in before.activities}
        after_activities = {type(activity): activity for activity in after.activities}

        for activity_type, activity in before_activities.items():
            if activity_type not in after_activities:
                await self.send_activity_log(after, activity, "stopped", log_channel)

        for activity_type, activity in after_activities.items():
            if activity_type not in before_activities:
                await self.send_activity_log(after, activity, "started", log_channel)
            elif activity != before_activities[activity_type]:
                await self.send_activity_log(after, activity, "updated", log_channel)

    async def send_activity_log(self, member: discord.Member, activity: discord.Activity, action: str, log_channel: discord.TextChannel):
        activity_type = type(activity).__name__
        embed = discord.Embed(
            title="Activity Update",
            description=f"{member.mention} has {action} an activity.",
            color=discord.Color.green() if action == "started" else discord.Color.red() if action == "stopped" else discord.Color.orange()
        )
        embed.add_field(name="Activity Type", value=activity_type, inline=True)
        embed.add_field(name="Activity Name", value=str(activity.name), inline=True)
        if isinstance(activity, discord.Game):
            embed.add_field(name="Details", value=f"Playing: {activity.name}", inline=False)
        elif isinstance(activity, discord.Streaming):
            embed.add_field(name="Details", value=f"Streaming: {activity.name}\nURL: {activity.url}", inline=False)
        elif isinstance(activity, discord.Spotify):
            embed.add_field(name="Details", value=f"Listening to: {activity.title} by {', '.join(activity.artists)}", inline=False)
        elif isinstance(activity, discord.Activity):
            embed.add_field(name="Details", value=f"Activity: {activity.name}", inline=False)
        embed.set_footer(text=f"User ID: {member.id}")

        await log_channel.send(embed=embed)

def setup(bot: Red):
    bot.add_cog(PresenceTracker(bot))
