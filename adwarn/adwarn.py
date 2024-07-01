import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
from datetime import datetime

class AdWarn(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)  # Replace with a unique identifier
        self.config.register_guild(warn_channel=None, thresholds={})
        self.config.register_member(warnings=[])

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def adwarn(self, ctx, user: discord.Member, *, reason: str):
        """Warn a user and send an embed to the default warning channel."""
        warn_channel_id = await self.config.guild(ctx.guild).warn_channel()
        if warn_channel_id:
            warn_channel = self.bot.get_channel(warn_channel_id)
            if warn_channel:
                # Store the warning
                warnings = await self.config.member(user).warnings()
                warning_time = datetime.utcnow().isoformat()
                warnings.append({
                    "reason": reason,
                    "moderator": ctx.author.id,
                    "time": warning_time,
                    "channel": ctx.channel.id
                })
                await self.config.member(user).warnings.set(warnings)

                # Create the embed message
                embed = discord.Embed(title="You were warned!", color=discord.Color.red())
                embed.add_field(name="User", value=user.mention, inline=True)
                embed.add_field(name="In", value=ctx.channel.mention, inline=True)
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
                embed.add_field(name="Time", value=warning_time, inline=False)
                embed.set_footer(text=f"Total warnings: {len(warnings)}")

                # Send the embed to the specified warning channel
                await warn_channel.send(embed=embed)

                # Send plain text message to the warning channel
                await warn_channel.send(f"{user.mention}")

                # Send confirmation embed to the command issuer
                confirmation_embed = discord.Embed(
                    title="Warning Issued",
                    description=f"{user.mention} has been warned for: {reason} in {ctx.channel.mention}",
                    color=discord.Color.green()
                )
                confirmation_message = await ctx.send(embed=confirmation_embed)
                await confirmation_message.delete(delay=3)

                # Check thresholds and take action if necessary
                await self.check_thresholds(ctx, user, len(warnings))
            else:
                error_embed = discord.Embed(
                    title="ErRoR 404",
                    description="Warning channel not found. Please set it again using `[p]warnset channel`.",
                    color=discord.Color.red()
                )
                error_message = await ctx.send(embed=error_embed)
                await error_message.delete(delay=3)
        else:
            error_embed = discord.Embed(
                title="ErRoR 404",
                description="No warning channel has been set. Please set it using `[p]warnset channel`.",
                color=discord.Color.red()
            )
            error_message = await ctx.send(embed=error_embed)
            await error_message.delete(delay=3)

        # Delete the command message after 3 seconds
        await ctx.message.delete(delay=3)

    async def check_thresholds(self, ctx, user, warning_count):
        thresholds = await self.config.guild(ctx.guild).thresholds()

        if warning_count in thresholds:
            action = thresholds[warning_count]
            if action == "kick":
                await ctx.guild.kick(user, reason="Reached warning threshold")
                await ctx.send(f"{user.mention} has been kicked for reaching {warning_count} warnings.")
            elif action == "ban":
                await ctx.guild.ban(user, reason="Reached warning threshold")
                await ctx.send(f"{user.mention} has been banned for reaching {warning_count} warnings.")
            elif action == "mute":
                # Implement your mute logic here
                await ctx.send(f"{user.mention} has been muted for reaching {warning_count} warnings.")
            # Add more actions as needed

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def removewarn(self, ctx, user: discord.Member, index: int):
        """Remove a specific warning from a user."""
        warnings = await self.config.member(user).warnings()
        if 0 <= index < len(warnings):
            removed_warning = warnings.pop(index)
            await self.config.member(user).warnings.set(warnings)

            warn_channel_id = await self.config.guild(ctx.guild).warn_channel()
            if warn_channel_id:
                warn_channel = self.bot.get_channel(warn_channel_id)
                if warn_channel:
                    # Create the embed message
                    embed = discord.Embed(title="AdWarn Removed", color=discord.Color.green())
                    embed.add_field(name="Warning", value=removed_warning["reason"], inline=False)
                    embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
                    embed.add_field(name="Removed Time", value=datetime.utcnow().isoformat(), inline=True)
                    embed.set_footer(text=f"Total warnings: {len(warnings)}")

                    # Send the embed to the specified warning channel
                    await warn_channel.send(embed=embed)
                else:
                    error_embed = discord.Embed(
                        title="ErRoR 404",
                        description="Warning channel not found. Please set it again using `[p]warnset channel`.",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=error_embed)
            else:
                error_embed = discord.Embed(
                    title="ErRoR 404",
                    description="No warning channel has been set. Please set it using `[p]warnset channel`.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=error_embed)
        else:
            error_embed = discord.Embed(
                title="ErRoR 404",
                description=f"Invalid warning index. {user.mention} has {len(warnings)} warnings.",
                color=discord.Color.red()
            )
            await ctx.send(embed=error_embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def warncount(self, ctx, user: discord.Member):
        """Get the total number of warnings a user has."""
        warnings = await self.config.member(user).warnings()
        embed = discord.Embed(
            title="Warning Count",
            description=f"{user.mention} has {len(warnings)} warnings.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clearwarns(self, ctx, user: discord.Member):
        """Clear all warnings for a user."""
        await self.config.member(user).warnings.set([])
        warn_channel_id = await self.config.guild(ctx.guild).warn_channel()
        if warn_channel_id:
            warn_channel = self.bot.get_channel(warn_channel_id)
            if warn_channel:
                # Create the embed message
                embed = discord.Embed(title="All Warnings Cleared", color=discord.Color.green())
                embed.add_field(name="User", value=user.mention, inline=True)
                embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
                embed.add_field(name="Cleared Time", value=datetime.utcnow().isoformat(), inline=True)

                # Send the embed to the specified warning channel
                await warn_channel.send(embed=embed)
            else:
                error_embed = discord.Embed(
                    title="ErRoR 404",
                    description="Warning channel not found. Please set it again using `[p]warnset channel`.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=error_embed)
        else:
            error_embed = discord.Embed(
                title="ErRoR 404",
                description="No warning channel has been set. Please set it using `[p]warnset channel`.",
                color=discord.Color.red()
            )
            await ctx.send(embed=error_embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def unadwarn(self, ctx, user: discord.Member):
        """Clear the most recent warning for a user."""
        warnings = await self.config.member(user).warnings()
        if warnings:
            removed_warning = warnings.pop()
            await self.config.member(user).warnings.set(warnings)

            warn_channel_id = await self.config.guild(ctx.guild).warn_channel()
            if warn_channel_id:
                warn_channel = self.bot.get_channel(warn_channel_id)
                if warn_channel:
                    # Create the embed message
                    embed = discord.Embed(title="Most Recent AdWarn Removed", color=discord.Color.green())
                    embed.add_field(name="Warning", value=removed_warning["reason"], inline=False)
                    embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
                    embed.add_field(name="Removed Time", value=datetime.utcnow().isoformat(), inline=True)
                    embed.set_footer(text=f"Total warnings: {len(warnings)}")

                    # Send the embed to the specified warning channel
                    await warn_channel.send(embed=embed)
                else:
                    error_embed = discord.Embed(
                        title="ErRoR 404",
                        description="Warning channel not found. Please set it again using `[p]warnset channel`.",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=error_embed)
            else:
                error_embed = discord.Embed(
                    title="ErRoR 404",
                    description="No warning channel has been set. Please set it using `[p]warnset channel`.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=error_embed)
        else:
            error_embed = discord.Embed(
                title="ErRoR 404",
                description=f"{user.mention} has no warnings.",
                color=discord.Color.red()
            )
            await ctx.send(embed=error_embed)

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
        embed = discord.Embed(
            title="Warning Channel Set",
            description=f"Warning channel has been set to {channel.mention}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @warnset.command()
    async def show(self, ctx):
        """Show the current warning channel."""
        channel_id = await self.config.guild(ctx.guild).warn_channel()
        if channel_id:
            channel = self.bot.get_channel(channel_id)
            embed = discord.Embed(
                title="Current Warning Channel",
                description=f"The current warning channel is {channel.mention}",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="No Warning Channel Set",
                description="No warning channel has been set.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @warnset.command()
    async def threshold(self, ctx, warning_count: int, action: str):
        """Set an action for a specific warning count threshold."""
        valid_actions = ["kick", "ban", "mute"]  # Add more actions as needed
        if action not in valid_actions:
            await ctx.send(f"Invalid action. Valid actions are: {', '.join(valid_actions)}")
            return

        thresholds = await self.config.guild(ctx.guild).thresholds()
        thresholds[warning_count] = action
        await self.config.guild(ctx.guild).thresholds.set(thresholds)
        await ctx.send(f"Set action '{action}' for reaching {warning_count} warnings.")
