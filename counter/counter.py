from redbot.core import commands, Config
import discord
from redbot.core.bot import Red
from redbot.core.commands import is_owner

class Counter(commands.Cog):
    """A cog to track various statistics for Red-DiscordBot"""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "command_count": 0,
            "unique_users": [],
            "command_usage": {},
        }
        self.config.register_guild(**default_guild)

    @commands.Cog.listener()
    async def on_command(self, ctx):
        async with self.config.guild(ctx.guild).all() as guild_data:
            guild_data["command_count"] += 1

            if ctx.author.id not in guild_data["unique_users"]:
                guild_data["unique_users"].append(ctx.author.id)

            if ctx.command.name not in guild_data["command_usage"]:
                guild_data["command_usage"][ctx.command.name] = {"count": 0, "users": {}}

            guild_data["command_usage"][ctx.command.name]["count"] += 1

            if ctx.author.id not in guild_data["command_usage"][ctx.command.name]["users"]:
                guild_data["command_usage"][ctx.command.name]["users"][ctx.author.id] = 0

            guild_data["command_usage"][ctx.command.name]["users"][ctx.author.id] += 1

    @commands.group()
    async def counter(self, ctx):
        """Group command for counting statistics"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @counter.command()
    async def users(self, ctx):
        """Display the total unique users"""
        guild_data = await self.config.guild(ctx.guild).all()
        unique_users_count = len(guild_data["unique_users"])

        embed = discord.Embed(title="Here's your requested count", color=discord.Color.green())
        embed.add_field(name="Total Unique Users", value=unique_users_count, inline=False)

        await ctx.send(embed=embed)

    @counter.command()
    async def servers(self, ctx):
        """Display the total servers"""
        server_count = len(self.bot.guilds)

        embed = discord.Embed(title="Here's your requested count", color=discord.Color.green())
        embed.add_field(name="Total Servers", value=server_count, inline=False)

        await ctx.send(embed=embed)

    @counter.command()
    async def commands(self, ctx):
        """Display the total commands"""
        guild_data = await self.config.guild(ctx.guild).all()

        embed = discord.Embed(title="Here's your requested count", color=discord.Color.green())
        embed.add_field(name="Total Commands", value=guild_data["command_count"], inline=False)

        await ctx.send(embed=embed)

    @counter.command()
    async def cogs(self, ctx):
        """Display the total cogs"""
        cog_count = len(self.bot.cogs)

        embed = discord.Embed(title="Here's your requested count", color=discord.Color.green())
        embed.add_field(name="Total Cogs", value=cog_count, inline=False)

        await ctx.send(embed=embed)

    @counter.command()
    @is_owner()
    async def totalcommands(self, ctx, user_id: int):
        """Display the commands used by a specific user ID"""
        guild_data = await self.config.guild(ctx.guild).all()
        user_commands = {}

        for command_name, usage_data in guild_data["command_usage"].items():
            if user_id in usage_data["users"]:
                user_commands[command_name] = usage_data["users"][user_id]

        if not user_commands:
            await ctx.send(f"No commands found for user ID {user_id}.")
            return

        sorted_commands = sorted(user_commands.items(), key=lambda item: item[1], reverse=True)
        user_stats = "\n".join([f"{cmd}: {count}" for cmd, count in sorted_commands])

        embed = discord.Embed(title="Here's your requested count", color=discord.Color.green())
        embed.add_field(name=f"Commands used by user ID {user_id}", value=user_stats, inline=False)

        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Counter(bot))
