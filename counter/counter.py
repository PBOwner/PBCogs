from redbot.core import commands, Config
import discord
from redbot.core.bot import Red
from redbot.core.commands import is_owner
from datetime import datetime

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
        self.color_index = 0
        self.colors = [0xff00ff, 0x0000ff, 0x00ff00]

    def get_next_color(self):
        color = self.colors[self.color_index]
        self.color_index = (self.color_index + 1) % len(self.colors)
        return color

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

    @commands.group(invoke_without_command=True)
    async def counter(self, ctx):
        """Group command for counting statistics"""
        await ctx.send_help(ctx.command)

    @counter.command()
    async def users(self, ctx):
        """Display the total number of users who can use the bot"""
        total_users = sum(len(guild.members) for guild in self.bot.guilds)

        embed = discord.Embed(title="Total Users", color=self.get_next_color())
        embed.add_field(name="Total Users", value=total_users, inline=True)
        embed.add_field(name="Time ran at", value=f"<t:{int(datetime.utcnow().timestamp())}:F>", inline=False)

        await ctx.send(embed=embed)

    @counter.command()
    async def servers(self, ctx):
        """Display the total servers"""
        server_count = len(self.bot.guilds)

        embed = discord.Embed(title="Total Servers", color=self.get_next_color())
        embed.add_field(name="Total Servers", value=server_count, inline=True)
        embed.add_field(name="Time ran at", value=f"<t:{int(datetime.utcnow().timestamp())}:F>", inline=False)

        await ctx.send(embed=embed)

    @counter.command()
    async def commands(self, ctx):
        """Display the total number of commands and subcommands the bot has"""
        total_commands = sum(1 for _ in self.bot.walk_commands())

        embed = discord.Embed(title="Total Commands", color=self.get_next_color())
        embed.add_field(name="Total Commands", value=total_commands, inline=True)
        embed.add_field(name="Time ran at", value=f"<t:{int(datetime.utcnow().timestamp())}:F>", inline=False)

        await ctx.send(embed=embed)

    @counter.command()
    async def cogs(self, ctx):
        """Display the total cogs"""
        cog_count = len(self.bot.cogs)

        embed = discord.Embed(title="Total Cogs", color=self.get_next_color())
        embed.add_field(name="Total Cogs", value=cog_count, inline=True)
        embed.add_field(name="Time ran at", value=f"<t:{int(datetime.utcnow().timestamp())}:F>", inline=False)

        await ctx.send(embed=embed)

    @counter.command()
    @is_owner()
    async def totalcommands(self, ctx, user_id: int):
        """Display the top 10 commands used by a specific user ID"""
        guild_data = await self.config.guild(ctx.guild).all()
        user_commands = {}

        for command_name, usage_data in guild_data["command_usage"].items():
            if user_id in usage_data["users"]:
                user_commands[command_name] = usage_data["users"][user_id]

        if not user_commands:
            await ctx.send(f"No commands found for user ID {user_id}.")
            return

        sorted_commands = sorted(user_commands.items(), key=lambda item: item[1], reverse=True)[:10]
        user_stats = "\n".join([f"{cmd}: {count}" for cmd, count in sorted_commands])

        embed = discord.Embed(title="Top 10 Commands", color=self.get_next_color())
        embed.add_field(name=f"Top 10 Commands used by user ID {user_id}", value=user_stats, inline=False)
        embed.add_field(name="Time ran at", value=f"<t:{int(datetime.utcnow().timestamp())}:F>", inline=False)

        await ctx.send(embed=embed)

    @counter.command()
    async def topusers(self, ctx):
        """Display the top 5 users and each command they ran"""
        guild_data = await self.config.guild(ctx.guild).all()
        user_command_counts = {}

        for command_name, usage_data in guild_data["command_usage"].items():
            for user_id, count in usage_data["users"].items():
                if user_id not in user_command_counts:
                    user_command_counts[user_id] = 0
                user_command_counts[user_id] += count

        top_users = sorted(user_command_counts.items(), key=lambda item: item[1], reverse=True)[:5]

        embed = discord.Embed(title="Top 5 Users", color=self.get_next_color())
        for user_id, _ in top_users:
            user = ctx.guild.get_member(user_id)
            if user:
                user_commands = [
                    f"{cmd}: {usage_data['users'][user_id]}"
                    for cmd, usage_data in guild_data["command_usage"].items()
                    if user_id in usage_data["users"]
                ]
                user_stats = "\n".join(user_commands)
                embed.add_field(name=user.display_name, value=user_stats, inline=False)

        embed.add_field(name="Time ran at", value=f"<t:{int(datetime.utcnow().timestamp())}:F>", inline=False)

        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Counter(bot))
