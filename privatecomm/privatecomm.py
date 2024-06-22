import discord
from redbot.core import commands, Config

class PrivateComm(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "bridge_channel": None
        }
        self.config.register_guild(**default_guild)
        self.user_message_cache = {}

    @commands.guild_only()
    @commands.admin()
    @commands.command()
    async def setbridge(self, ctx, channel: discord.TextChannel):
        """Set the channel where DMs will be forwarded."""
        await self.config.guild(ctx.guild).bridge_channel.set(channel.id)
        await ctx.send(f"Bridge channel set to {channel.mention}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None and not message.author.bot:
            # Message is a DM
            for guild in self.bot.guilds:
                bridge_channel_id = await self.config.guild(guild).bridge_channel()
                if bridge_channel_id:
                    bridge_channel = guild.get_channel(bridge_channel_id)
                    if bridge_channel:
                        embed = discord.Embed(
                            title="New DM",
                            description=message.content,
                            color=discord.Color.blue()
                        )
                        embed.set_author(name=message.author, icon_url=message.author.avatar_url)
                        await bridge_channel.send(embed=embed)
                        self.user_message_cache[bridge_channel.id] = message.author.id
                        break

        elif message.guild is not None and not message.author.bot:
            # Message is in a guild channel
            bridge_channel_id = await self.config.guild(message.guild).bridge_channel()
            if bridge_channel_id and message.channel.id == bridge_channel_id:
                user_id = self.user_message_cache.get(message.channel.id)
                if user_id:
                    user = self.bot.get_user(user_id)
                    if user:
                        await user.send(f"{message.author}: {message.content}")

def setup(bot):
    bot.add_cog(PrivateComm(bot))
