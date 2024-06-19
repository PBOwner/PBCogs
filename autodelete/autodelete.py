import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
from datetime import datetime, timedelta

class AutoDelete(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)  # Replace with a unique identifier
        self.config.register_guild(auto_delete=False, log_channel=None)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def adtoggle(self, ctx, state: bool):
        """Toggle automatic deletion of user messages."""
        await self.config.guild(ctx.guild).auto_delete.set(state)

        state_text = "enabled" if state else "disabled"
        embed = discord.Embed(
            title="AutoDelete Toggled",
            description=f"Automatic deletion of user messages has been {state_text}.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setlogchannel(self, ctx, channel: discord.TextChannel):
        """Set the logging channel for automatic deletes."""
        await self.config.guild(ctx.guild).log_channel.set(channel.id)
        embed = discord.Embed(
            title="Log Channel Set",
            description=f"Log channel has been set to {channel.mention}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def showlogchannel(self, ctx):
        """Show the current logging channel for automatic deletes."""
        channel_id = await self.config.guild(ctx.guild).log_channel()
        if channel_id:
            channel = self.bot.get_channel(channel_id)
            embed = discord.Embed(
                title="Current Log Channel",
                description=f"The current log channel is {channel.mention}",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="No Log Channel Set",
                description="No log channel has been set.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        auto_delete = await self.config.guild(message.guild).auto_delete()
        if auto_delete:
            fourteen_days_ago = datetime.utcnow() - timedelta(days=14)
            if message.created_at > fourteen_days_ago:
                try:
                    await message.delete()
                    # Log the deletion
                    log_channel_id = await self.config.guild(message.guild).log_channel()
                    if log_channel_id:
                        log_channel = self.bot.get_channel(log_channel_id)
                        if log_channel:
                            embed = discord.Embed(
                                title="Message Deleted",
                                description=f"A message from {message.author.mention} was automatically deleted.",
                                color=discord.Color.orange()
                            )
                            embed.add_field(name="Channel", value=message.channel.mention, inline=True)
                            embed.add_field(name="Content", value=message.content, inline=False)
                            embed.set_footer(text=f"Message ID: {message.id}")
                            await log_channel.send(embed=embed)
                except discord.Forbidden:
                    error_embed = discord.Embed(
                        title="ErRoR 404",
                        description=f"Missing permissions to delete messages in {message.channel.mention}.",
                        color=discord.Color.red()
                    )
                    await message.channel.send(embed=error_embed, delete_after=10)
                except discord.HTTPException as e:
                    error_embed = discord.Embed(
                        title="ErRoR 404",
                        description=f"Failed to delete messages in {message.channel.mention}: {str(e)}",
                        color=discord.Color.red()
                    )
                    await message.channel.send(embed=error_embed, delete_after=10)

def setup(bot: Red):
    bot.add_cog(AutoDelete(bot))
