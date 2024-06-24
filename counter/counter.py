import random
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

    def get_random_color(self):
        return random.randint(0, 0xFFFFFF)

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

    @commands.group(name="count", invoke_without_command=True)
    async def count(self, ctx):
        """Group command for counting statistics"""
        await ctx.send_help(ctx.command)

    @count.command()
    async def users(self, ctx):
        """Display the total number of users who can use the bot"""
        total_users = sum(len(guild.members) for guild in self.bot.guilds)
        response = f"Total Users: {total_users}"

        if ctx.guild is None:
            await ctx.send(response)
        else:
            embed = discord.Embed(title="Total Users", color=self.get_random_color())
            embed.add_field(name="Total Users", value=total_users, inline=True)
            await ctx.send(embed=embed)

    @count.command()
    async def servers(self, ctx):
        """Display the total servers"""
        server_count = len(self.bot.guilds)
        response = f"Total Servers: {server_count}"

        if ctx.guild is None:
            await ctx.send(response)
        else:
            embed = discord.Embed(title="Total Servers", color=self.get_random_color())
            embed.add_field(name="Total Servers", value=server_count, inline=True)
            await ctx.send(embed=embed)

    @count.command(name="commands")
    async def count_commands(self, ctx):
        """Display the total number of commands and subcommands the bot has"""
        total_commands = sum(1 for _ in self.bot.walk_commands())
        top_commands = sum(1 for cmd in self.bot.commands)
        subcommands = total_commands - top_commands

        user_commands = []
        mod_commands = []
        admin_commands = []
        owner_commands = []
        bot_owner_commands = []

        for cmd in self.bot.walk_commands():
            if not cmd.hidden:
                user_commands.append(cmd.name)
                if cmd.requires.mod_or_permissions():
                    mod_commands.append(cmd.name)
                if cmd.requires.admin_or_permissions():
                    admin_commands.append(cmd.name)
                if cmd.requires.is_owner():
                    bot_owner_commands.append(cmd.name)

        response = (
            f"Total Commands: {total_commands}\n"
            f"Top-Level Commands: {top_commands}\n"
            f"SubCommands: {subcommands}\n"
            f"User Commands: {', '.join(user_commands)}\n"
            f"Mod Commands: {', '.join(mod_commands)}\n"
            f"Admin Commands: {', '.join(admin_commands)}\n"
            f"Guild Owner Commands: {', '.join(owner_commands)}\n"
            f"Bot Owner Commands: {', '.join(bot_owner_commands)}"
        )

        if ctx.guild is None:
            await ctx.send(response)
        else:
            embed = discord.Embed(title="Total Commands", color=self.get_random_color())
            embed.add_field(name="Total Commands", value=total_commands, inline=True)
            embed.add_field(name="Top-Level Commands", value=top_commands, inline=True)
            embed.add_field(name="SubCommands", value=subcommands, inline=True)
            embed.add_field(name="User Commands", value=', '.join(user_commands), inline=False)
            embed.add_field(name="Mod Commands", value=', '.join(mod_commands), inline=False)
            embed.add_field(name="Admin Commands", value=', '.join(admin_commands), inline=False)
            embed.add_field(name="Guild Owner Commands", value=', '.join(owner_commands), inline=False)
            embed.add_field(name="Bot Owner Commands", value=', '.join(bot_owner_commands), inline=False)
            await ctx.send(embed=embed)

    @count.command()
    async def cogs(self, ctx):
        """Display the total cogs"""
        cog_count = len(self.bot.cogs)
        response = f"Total Cogs: {cog_count}"

        if ctx.guild is None:
            await ctx.send(response)
        else:
            embed = discord.Embed(title="Total Cogs", color=self.get_random_color())
            embed.add_field(name="Total Cogs", value=cog_count, inline=True)
            await ctx.send(embed=embed)

    @count.command()
    async def total(self, ctx):
        """Display the top 10 commands used globally"""
        all_guild_data = await self.config.all_guilds()
        global_command_usage = {}

        for guild_data in all_guild_data.values():
            for command_name, usage_data in guild_data["command_usage"].items():
                if command_name not in global_command_usage:
                    global_command_usage[command_name] = 0
                global_command_usage[command_name] += usage_data["count"]

        if not global_command_usage:
            await ctx.send("No commands found.")
            return

        sorted_commands = sorted(global_command_usage.items(), key=lambda item: item[1], reverse=True)[:10]
        command_stats = "\n".join([f"{cmd}: {count}" for cmd, count in sorted_commands])
        response = f"Top 10 Commands Globally:\n{command_stats}"

        if ctx.guild is None:
            await ctx.send(response)
        else:
            embed = discord.Embed(title="Top 10 Commands Globally", color=self.get_random_color())
            embed.add_field(name="Command Usage", value=command_stats, inline=False)
            await ctx.send(embed=embed)

    @count.command()
    @is_owner()
    async def stats(self, ctx):
        """Display all statistics in one embed with a random color"""
        total_users = sum(len(guild.members) for guild in self.bot.guilds)
        server_count = len(self.bot.guilds)
        total_commands = sum(1 for _ in self.bot.walk_commands())
        cog_count = len(self.bot.cogs)

        response = (
            f"Bot Statistics:\n"
            f"Total Users: {total_users}\n"
            f"Total Servers: {server_count}\n"
            f"Total Commands: {total_commands}\n"
            f"Total Cogs: {cog_count}"
        )

        if ctx.guild is None:
            await ctx.send(response)
        else:
            embed = discord.Embed(title="Bot Statistics", color=self.get_random_color())
            embed.add_field(name="Total Users", value=total_users, inline=True)
            embed.add_field(name="Total Servers", value=server_count, inline=True)
            embed.add_field(name="Total Commands", value=total_commands, inline=True)
            embed.add_field(name="Total Cogs", value=cog_count, inline=True)
            await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Counter(bot))
