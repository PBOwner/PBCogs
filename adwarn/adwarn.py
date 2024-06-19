import discord
from redbot.core import commands, Config
from redbot.core.bot import Red

class AdWarn(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)  # Replace with a unique identifier
        self.config.register_guild(warn_channel=None)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def adwarn(self, ctx, user: discord.Member, *, reason: str):
        """Warn a user and send an embed to the default warning channel."""
        channel_id = await self.config.guild(ctx.guild).warn_channel()
        if channel_id:
            channel = self.bot.get_channel(channel_id)
            if channel:
                # Create the embed message
                embed = discord.Embed(title="You were warned!", color=discord.Color.red())
                embed.add_field(name="User", value=user.mention, inline=True)
                embed.add_field(name="Reason", value=reason, inline=False)

                # Send the embed to the specified channel
                await channel.send(embed=embed)
                await ctx.send(f"{user.mention} has been warned for: {reason}", delete_after=5)  # Optional: delete the confirmation message after 5 seconds
            else:
                await ctx.send("Warning channel not found. Please set it again using `[p]warnset channel`.")
        else:
            await ctx.send("No warning channel has been set. Please set it using `[p]warnset channel`.")

    @commands.group()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def warnset(self, ctx):
        """Settings for the warning system."""
        pass

    @warnset.command()
    async def channel(self, ctx, channel: discord.TextChannel):
        """Set the default channel for warnings."""
        await self.config.guild(ctx.guild).warn_channel.set(channel.id)
        await ctx.send(f"Warning channel has been set to {channel.mention}")

    @warnset.command()
    async def show(self, ctx):
        """Show the current warning channel."""
        channel_id = await self.config.guild(ctx.guild).warn_channel()
        if channel_id:
            channel = self.bot.get_channel(channel_id)
            await ctx.send(f"The current warning channel is {channel.mention}")
        else:
            await ctx.send("No warning channel has been set.")

def setup(bot: Red):
    bot.add_cog(AdWarn(bot))
