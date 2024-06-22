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
            "channel_id": None,
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

    @commands.group(invoke_without_command=True)
    async def counter(self, ctx):
        """Group command for counting statistics"""
        await ctx.send_help(ctx.command)

    @counter.command()
    async def users(self, ctx):
        """Display the total number of users who can use the bot"""
        total_users = sum(len(guild.members) for guild in self.bot.guilds)

        embed = discord.Embed(title="Total Users", color=discord.Color.green())
        embed.add_field(name="Total Users", value=total_users, inline=False)

        await ctx.send(embed=embed)

    @counter.command()
    async def servers(self, ctx):
        """Display the total servers"""
        server_count = len(self.bot.guilds)

        embed = discord.Embed(title="Total Servers", color=discord.Color.green())
        embed.add_field(name="Total Servers", value=server_count, inline=False)

        await ctx.send(embed=embed)

    @counter.command()
    async def commands(self, ctx):
        """Display the total number of commands and subcommands the bot has"""
        total_commands = sum(1 for _ in self.bot.walk_commands())

        embed = discord.Embed(title="Total Commands", color=discord.Color.green())
        embed.add_field(name="Total Commands", value=total_commands, inline=False)

        await ctx.send(embed=embed)

    @counter.command()
    async def cogs(self, ctx):
        """Display the total cogs"""
        cog_count = len(self.bot.cogs)

        embed = discord.Embed(title="Total Cogs", color=discord.Color.green())
        embed.add_field(name="Total Cogs", value=cog_count, inline=False)

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

        embed = discord.Embed(title="Top 10 Commands", color=discord.Color.green())
        embed.add_field(name=f"Top 10 Commands used by user ID {user_id}", value=user_stats, inline=False)

        await ctx.send(embed=embed)

    @counter.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def setchannel(self, ctx, channel: discord.TextChannel):
        """Set the channel for dynamically updating statistics"""
        if not ctx.guild:
            await ctx.send("This command can only be used in a server.")
            return

        await self.config.guild(ctx.guild).channel_id.set(channel.id)
        await ctx.send(f"Channel set to {channel.mention} for dynamic statistics.")

    async def update_dynamic_embed(self):
        for guild in self.bot.guilds:
            channel_id = await self.config.guild(guild).channel_id()
            if channel_id:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    total_users = sum(len(guild.members) for guild in self.bot.guilds)
                    server_count = len(self.bot.guilds)
                    total_commands = sum(1 for _ in self.bot.walk_commands())
                    cog_count = len(self.bot.cogs)

                    # Calculate top 5 users with the most commands run
                    user_command_counts = {}
                    for usage_data in (await self.config.all_guilds()).values():
                        for command_name, data in usage_data["command_usage"].items():
                            for user_id, count in data["users"].items():
                                if user_id not in user_command_counts:
                                    user_command_counts[user_id] = 0
                                user_command_counts[user_id] += count

                    top_users = sorted(user_command_counts.items(), key=lambda item: item[1], reverse=True)[:5]
                    top_users_stats = "\n".join([f"<@{user_id}>: {count}" for user_id, count in top_users])

                    embed = discord.Embed(title="Bot Stats", color=discord.Color.green())
                    embed.add_field(name="Total Users", value=total_users, inline=False)
                    embed.add_field(name="Total Servers", value=server_count, inline=False)
                    embed.add_field(name="Total Commands", value=total_commands, inline=False)
                    embed.add_field(name="Total Cogs", value=cog_count, inline=False)
                    embed.add_field(name="Top 5 Users", value=top_users_stats, inline=False)

                    message = None
                    async for msg in channel.history(limit=10):
                        if msg.author == self.bot.user and msg.embeds and msg.embeds[0].title == "Bot Stats":
                            message = msg
                            break

                    if message:
                        await message.edit(embed=embed)
                    else:
                        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.update_dynamic_embed()

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.update_dynamic_embed()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        await self.update_dynamic_embed()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.update_dynamic_embed()

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self.update_dynamic_embed()

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        await self.update_dynamic_embed()

def setup(bot):
    bot.add_cog(Counter(bot))
