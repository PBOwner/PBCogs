import discord
from redbot.core import commands, Config

class PrivateComm(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "bridge_channels": {}
        }
        self.config.register_guild(**default_guild)

    @commands.guild_only()
    @commands.admin()
    @commands.command()
    async def setbridge(self, ctx, channel: discord.TextChannel, user_id: int):
        """Set the channel where DMs from a specific user will be forwarded."""
        async with self.config.guild(ctx.guild).bridge_channels() as bridge_channels:
            bridge_channels[str(channel.id)] = user_id
        await ctx.send(f"Bridge channel set to {channel.mention} for user ID {user_id}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None and not message.author.bot:
            # Message is a DM
            for guild in self.bot.guilds:
                bridge_channels = await self.config.guild(guild).bridge_channels()
                for channel_id, user_id in bridge_channels.items():
                    if message.author.id == user_id:
                        bridge_channel = guild.get_channel(int(channel_id))
                        if bridge_channel:
                            embed = discord.Embed(
                                title="New DM",
                                description=message.content,
                                color=discord.Color.blue()
                            )
                            embed.set_author(name=message.author, icon_url=message.author.avatar_url)
                            await bridge_channel.send(embed=embed)
                            break

        elif message.guild is not None and not message.author.bot:
            # Message is in a guild channel
            bridge_channels = await self.config.guild(message.guild).bridge_channels()
            user_id = bridge_channels.get(str(message.channel.id))
            if user_id:
                user = self.bot.get_user(user_id)
                if user:
                    await user.send(f"{message.author}: {message.content}")
