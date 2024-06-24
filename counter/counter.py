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
        """Display the total number of commands each permission level can run"""
        user_commands = 0
        mod_commands = 0
        admin_commands = 0
        owner_commands = 0
        bot_owner_commands = 0

        for cmd in self.bot.walk_commands():
            try:
                if await cmd.can_run(ctx):
                    if await ctx.bot.is_owner(ctx.author):
                        bot_owner_commands += 1
                    elif ctx.author.guild_permissions.administrator:
                        admin_commands += 1
                    elif ctx.author.guild_permissions.manage_messages:
                        mod_commands += 1
                    elif ctx.guild is not None and ctx.guild.owner_id == ctx.author.id:
                        owner_commands += 1
                    else:
                        user_commands += 1
            except commands.CheckFailure:
                continue

        response = (
            f"Bot Owner Commands: {bot_owner_commands}\n"
            f"Admin Commands: {admin_commands}\n"
            f"Mod Commands: {mod_commands}\n"
            f"Owner Commands: {owner_commands}\n"
            f"User Commands: {user_commands}\n"
        )

        if ctx.guild is None:
            await ctx.send(response)
        else:
            embed = discord.Embed(title="Commands Count by Permission Level", color=self.get_random_color())
            embed.add_field(name="Bot Owner Commands", value=bot_owner_commands, inline=True)
            embed.add_field(name="Admin Commands", value=admin_commands, inline=True)
            embed.add_field(name="Mod Commands", value=mod_commands, inline=True)
            embed.add_field(name="Owner Commands", value=owner_commands, inline=True)
            embed.add_field(name="User Commands", value=user_commands, inline=True)
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
        """Display the total number of base commands the bot has"""
        base_commands = [cmd for cmd in self.bot.commands if not isinstance(cmd, commands.Group)]
        total_base_commands = len(base_commands)
        response = f"Total Base Commands: {total_base_commands}"

        if ctx.guild is None:
            await ctx.send(response)
        else:
            embed = discord.Embed(title="Total Base Commands", color=self.get_random_color())
            embed.add_field(name="Total Base Commands", value=total_base_commands, inline=True)
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
