import discord
from redbot.core import commands, Config

class Comm(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)  # Unique identifier
        default_guild = {"linked_channels": {}}
        self.config.register_guild(**default_guild)

    @commands.group()
    async def comm(self, ctx):
        """Group command for managing private communication channels."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @comm.command(name="open")
    async def comm_open(self, ctx, channel_id: int):
        """Open a private communication channel between your DMs and a server channel."""
        channel = self.bot.get_channel(channel_id)
        if not channel:
            await ctx.send("Invalid channel ID.")
            return

        guild = channel.guild
        async with self.config.guild(guild).linked_channels() as linked_channels:
            linked_channels[ctx.author.id] = channel_id

        await ctx.send(f"Private communication channel opened with {channel.mention}.")

    @comm.command(name="close")
    async def comm_close(self, ctx):
        """Close the private communication channel."""
        guilds = self.bot.guilds
        found = False
        for guild in guilds:
            async with self.config.guild(guild).linked_channels() as linked_channels:
                if ctx.author.id in linked_channels:
                    del linked_channels[ctx.author.id]
                    await ctx.send("Private communication channel closed.")
                    found = True
                    break
        if not found:
            await ctx.send("No private communication channel to close.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild:
            return  # Ignore messages sent in guilds

        async with self.config.all_guilds() as all_guilds:
            for guild_id, data in all_guilds.items():
                linked_channels = data.get("linked_channels", {})
                if message.author.id in linked_channels:
                    channel_id = linked_channels[message.author.id]
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        await channel.send(f"**DM from {message.author}**: {message.content}")
                    break

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild:
            return  # Ignore DMs

        async with self.config.guild(message.guild).linked_channels() as linked_channels:
            for user_id, channel_id in linked_channels.items():
                if message.channel.id == channel_id:
                    user = self.bot.get_user(user_id)
                    if user:
                        await user.send(f"**Message from {message.guild.name} #{message.channel.name}**: {message.content}")
                    break

def setup(bot):
    bot.add_cog(Comm(bot))
