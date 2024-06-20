import discord
from redbot.core import commands, Config
from redbot.core.bot import Red

class GameTracker(commands.Cog):
    """Cog to track when users start or stop playing a specific game."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567894, force_registration=True)
        default_guild = {
            "log_channel": None,
            "tracked_games": []
        }
        self.config.register_guild(**default_guild)

    @commands.group()
    async def gametracker(self, ctx: commands.Context):
        """Base command for game tracking."""
        pass

    @gametracker.command()
    @commands.has_permissions(manage_guild=True)
    async def setlogchannel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the channel where game activity updates will be logged."""
        await self.config.guild(ctx.guild).log_channel.set(channel.id)
        await ctx.send(f"Log channel set to {channel.mention}")

    @gametracker.command()
    @commands.has_permissions(manage_guild=True)
    async def addgame(self, ctx: commands.Context, *, game_name: str):
        """Add a game to the tracking list."""
        async with self.config.guild(ctx.guild).tracked_games() as tracked_games:
            if game_name not in tracked_games:
                tracked_games.append(game_name)
                await ctx.send(f"Game '{game_name}' added to the tracking list.")
            else:
                await ctx.send(f"Game '{game_name}' is already being tracked.")

    @gametracker.command()
    @commands.has_permissions(manage_guild=True)
    async def removegame(self, ctx: commands.Context, *, game_name: str):
        """Remove a game from the tracking list."""
        async with self.config.guild(ctx.guild).tracked_games() as tracked_games:
            if game_name in tracked_games:
                tracked_games.remove(game_name)
                await ctx.send(f"Game '{game_name}' removed from the tracking list.")
            else:
                await ctx.send(f"Game '{game_name}' is not being tracked.")

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        log_channel_id = await self.config.guild(after.guild).log_channel()
        if not log_channel_id:
            return

        log_channel = after.guild.get_channel(log_channel_id)
        if not log_channel:
            return

        tracked_games = await self.config.guild(after.guild).tracked_games()
        before_games = {activity.name for activity in before.activities if isinstance(activity, discord.Game)}
        after_games = {activity.name for activity in after.activities if isinstance(activity, discord.Game)}

        started_games = after_games - before_games
        stopped_games = before_games - after_games

        for game in started_games:
            if game in tracked_games:
                embed = discord.Embed(
                    title="Game Started",
                    description=f"{after.mention} has started playing {game}.",
                    color=discord.Color.green()
                )
                embed.set_footer(text=f"User ID: {after.id}")
                await log_channel.send(embed=embed)

        for game in stopped_games:
            if game in tracked_games:
                embed = discord.Embed(
                    title="Game Stopped",
                    description=f"{after.mention} has stopped playing {game}.",
                    color=discord.Color.red()
                )
                embed.set_footer(text=f"User ID: {after.id}")
                await log_channel.send(embed=embed)

def setup(bot: Red):
    bot.add_cog(GameTracker(bot))
