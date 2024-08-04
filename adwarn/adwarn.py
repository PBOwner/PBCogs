import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
from datetime import timedelta, datetime
import re
import uuid
import asyncio

class AdWarn(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)  # Replace with a unique identifier
        self.config.register_guild(warn_channel=None, tholds={}, warnings_issued={}, mod_warnings={}, softban_duration=120, timeout_duration=120, weekly_stats={}, monthly_stats={})
        self.config.register_member(warnings=[], untimeout_time=None)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def adwarn(self, ctx, user: discord.Member, *, reason: str):
        """Warn a user and send an embed to the default warning channel."""
        warn_channel_id = await self.config.guild(ctx.guild).warn_channel()
        if warn_channel_id:
            warn_channel = self.bot.get_channel(warn_channel_id)
            if warn_channel:
                # Store the warning with a UUID
                warnings = await self.config.member(user).warnings()
                warning_time = discord.utils.utcnow()
                warning_id = str(uuid.uuid4())
                warnings.append({
                    "id": warning_id,
                    "reason": reason,
                    "moderator": ctx.author.id,
                    "time": warning_time.isoformat(),
                    "channel": ctx.channel.id
                })
                await self.config.member(user).warnings.set(warnings)

                # Increment the count of warnings issued by the moderator for the current server
                warnings_issued = await self.config.guild(ctx.guild).warnings_issued()
                if str(ctx.author.id) not in warnings_issued:
                    warnings_issued[str(ctx.author.id)] = 0
                warnings_issued[str(ctx.author.id)] += 1
                await self.config.guild(ctx.guild).warnings_issued.set(warnings_issued)

                # Store the details of the warning issued by the moderator
                mod_warnings = await self.config.guild(ctx.guild).mod_warnings()
                if str(ctx.author.id) not in mod_warnings:
                    mod_warnings[str(ctx.author.id)] = []
                mod_warnings[str(ctx.author.id)].append({
                    "user": user.id,
                    "reason": reason,
                    "time": warning_time.isoformat(),
                    "channel": ctx.channel.id
                })
                await self.config.guild(ctx.guild).mod_warnings.set(mod_warnings)

                # Create the embed message
                timestamp = int(warning_time.timestamp())
                embed = discord.Embed(title="New AdWarn", color=discord.Color.red())
                embed.add_field(name="<:user:1268083437768671303> | User", value=user.mention, inline=True)
                embed.add_field(name="<:channel:1268083439651913819> | Warned In", value=ctx.channel.mention, inline=True)
                embed.add_field(name="<:reason:1268083436598591539> | Reason", value=reason, inline=False)
                embed.add_field(name="<:mod:1268083442193662024> | Moderator", value=ctx.author.mention, inline=True)
                embed.add_field(name="<:time:1268083440864198676> | Time", value=f"<t:{timestamp}:F>", inline=False)
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
                    title="Error 404",
                    description="Warning channel not found. Please set it again using `[p]warnset channel`.",
                    color=discord.Color.red()
                )
                error_message = await ctx.send(embed=error_embed)
                await error_message.delete(delay=3)
        else:
            error_embed = discord.Embed(
                title="Error 404",
                description="No warning channel has been set. Please set it using `[p]warnset channel`.",
                color=discord.Color.red()
            )
            error_message = await ctx.send(embed=error_embed)
            await error_message.delete(delay=3)

        # Delete the command message after 3 seconds
        await ctx.message.delete(delay=3)

    async def check_thresholds(self, ctx, user, warning_count):
        tholds = await self.config.guild(ctx.guild).tholds()
        softban_duration = await self.config.guild(ctx.guild).softban_duration()
        timeout_duration = await self.config.guild(ctx.guild).timeout_duration()

        for threshold_id, threshold in tholds.items():
            if threshold["count"] == warning_count:
                action = threshold["action"]
                if action == "kick":
                    await ctx.guild.kick(user, reason="Reached warning threshold")
                elif action == "ban":
                    await ctx.guild.ban(user, reason="Reached warning threshold")
                elif action == "timeout":
                    await self.timeout_user(ctx, user, timeout_duration)
                    if timeout_duration:
                        await self.schedule_untimeout(ctx, user, timeout_duration)
                elif action == "softban":
                    await ctx.guild.ban(user, reason="Reached warning threshold", delete_message_days=softban_duration)
                    await ctx.guild.unban(user, reason="Softban duration expired")

    def parse_duration(self, duration_str):
        """Parse a duration string and return the duration in minutes."""
        match = re.match(r"(\d+)([mh])", duration_str)
        if match:
            value, unit = match.groups()
            value = int(value)
            if unit == "h":
                return value * 60  # Convert hours to minutes
            elif unit == "m":
                return value  # Minutes
        return None

    async def timeout_user(self, ctx, user: discord.Member, duration: int = 120):
        if duration:
            timeout_until = discord.utils.utcnow() + timedelta(minutes=duration)
            await user.edit(timed_out_until=timeout_until, reason="Reached warning threshold")
            await self.config.member(user).untimeout_time.set(timeout_until.isoformat())

    async def schedule_untimeout(self, ctx, user, duration):
        untimeout_time = discord.utils.utcnow() + timedelta(minutes=duration)
        await self.config.member(user).untimeout_time.set(untimeout_time.isoformat())

    @commands.Cog.listener()
    async def on_ready(self):
        await self.check_untimeout_times()

    async def check_untimeout_times(self):
        for guild in self.bot.guilds:
            for member in guild.members:
                untimeout_time = await self.config.member(member).untimeout_time()
                if untimeout_time:
                    untimeout_time = datetime.fromisoformat(untimeout_time)
                    if discord.utils.utcnow() >= untimeout_time:
                        await self.untimeout_user(member)
                        await self.config.member(member).untimeout_time.clear()

    async def untimeout_user(self, user: discord.Member):
        await user.edit(timed_out_until=None, reason="Timeout duration expired")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def removewarn(self, ctx, user: discord.Member, warning_id: str):
        """Remove a specific warning from a user by its UUID."""
        warnings = await self.config.member(user).warnings()
        warning_to_remove = next((warning for warning in warnings if warning["id"] == warning_id), None)

        if warning_to_remove:
            warnings.remove(warning_to_remove)
            await self.config.member(user).warnings.set(warnings)

            warn_channel_id = await self.config.guild(ctx.guild).warn_channel()
            if warn_channel_id:
                warn_channel = self.bot.get_channel(warn_channel_id)
                if warn_channel:
                    # Create the embed message
                    embed = discord.Embed(title="AdWarn Removed", color=discord.Color.green())
                    embed.add_field(name="<:reason:1268083436598591539> | Warning", value=warning_to_remove["reason"], inline=False)
                    embed.add_field(name="<:mod:1268083442193662024> | Moderator", value=ctx.author.mention, inline=True)
                    embed.add_field(name="<:time:1268083440864198676> | Removed Time", value=f"<t:{int(discord.utils.utcnow().timestamp())}:F>", inline=True)
                    embed.set_footer(text=f"Total warnings: {len(warnings)}")

                    # Send the embed to the specified warning channel
                    await warn_channel.send(embed=embed)
                else:
                    error_embed = discord.Embed(
                        title="Error 404",
                        description="Warning channel not found. Please set it again using `[p]warnset channel`.",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=error_embed)
            else:
                error_embed = discord.Embed(
                    title="Error 404",
                    description="No warning channel has been set. Please set it using `[p]warnset channel`.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=error_embed)
        else:
            error_embed = discord.Embed(
                title="Error 404",
                description=f"Warning with ID {warning_id} not found.",
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

        for warning in warnings:
            timestamp = int(datetime.fromisoformat(warning['time']).timestamp())
            embed.add_field(
                name=f"Warning ID: {warning['id']}",
                value=f"<:reason:1268083436598591539> | Reason: {warning['reason']}\n<:mod:1268083442193662024> | Moderator: <@{warning['moderator']}>\n<:time:1268083440864198676> | Time: <t:{timestamp}:F>",
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clearwarns(self, ctx, user: discord.User):
        """Clear all warnings for a user."""
        await self.config.member_from_ids(ctx.guild.id, user.id).warnings.set([])
        warn_channel_id = await self.config.guild(ctx.guild).warn_channel()
        if (warn_channel_id):
            warn_channel = self.bot.get_channel(warn_channel_id)
            if warn_channel:
                # Create the embed message
                embed = discord.Embed(title="All Warnings Cleared", color=discord.Color.green())
                embed.add_field(name="<:user:1268083437768671303> | User", value=user.mention, inline=True)
                embed.add_field(name="<:mod:1268083442193662024> | Moderator", value=ctx.author.mention, inline=True)
                embed.add_field(name="<:time:1268083440864198676> | Cleared Time", value=f"<t:{int(discord.utils.utcnow().timestamp())}:F>", inline=True)

                # Send the embed to the specified warning channel
                await warn_channel.send(embed=embed)
            else:
                error_embed = discord.Embed(
                    title="Error 404",
                    description="Warning channel not found. Please set it again using `[p]warnset channel`.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=error_embed)
        else:
            error_embed = discord.Embed(
                title="Error 404",
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
                    embed.add_field(name="<:reason:1268083436598591539> | Warning", value=removed_warning["reason"], inline=False)
                    embed.add_field(name="<:mod:1268083442193662024> | Moderator", value=ctx.author.mention, inline=True)
                    embed.add_field(name="<:time:1268083440864198676> | Removed Time", value=f"<t:{int(discord.utils.utcnow().timestamp())}:F>", inline=True)
                    embed.set_footer(text=f"Total warnings: {len(warnings)}")

                    # Send the embed to the specified warning channel
                    await warn_channel.send(embed=embed)
                else:
                    error_embed = discord.Embed(
                        title="Error 404",
                        description="Warning channel not found. Please set it again using `[p]warnset channel`.",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=error_embed)
            else:
                error_embed = discord.Embed(
                    title="Error 404",
                    description="No warning channel has been set. Please set it using `[p]warnset channel`.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=error_embed)
        else:
            error_embed = discord.Embed(
                title="Error 404",
                description=f"{user.mention} has no warnings.",
                color=discord.Color.red()
            )
            await ctx.send(embed=error_embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def editaw(self, ctx, user: discord.Member, warning_id: str, *, new_reason: str):
        """Edit a specific warning by its UUID."""
        warnings = await self.config.member(user).warnings()
        warning_to_edit = next((warning for warning in warnings if warning["id"] == warning_id), None)

        if warning_to_edit:
            warning_to_edit["reason"] = new_reason
            await self.config.member(user).warnings.set(warnings)

            warn_channel_id = await self.config.guild(ctx.guild).warn_channel()
            if warn_channel_id:
                warn_channel = self.bot.get_channel(warn_channel_id)
                if warn_channel:
                    # Create the embed message
                    embed = discord.Embed(title="AdWarn Edited", color=discord.Color.orange())
                    embed.add_field(name="<:reason:1268083436598591539> | Warning", value=new_reason, inline=False)
                    embed.add_field(name="<:mod:1268083442193662024> | Moderator", value=ctx.author.mention, inline=True)
                    embed.add_field(name="<:time:1268083440864198676> | Edited Time", value=f"<t:{int(discord.utils.utcnow().timestamp())}:F>", inline=True)
                    embed.set_footer(text=f"Total warnings: {len(warnings)}")

                    # Send the embed to the specified warning channel
                    await warn_channel.send(embed=embed)
                else:
                    error_embed = discord.Embed(
                        title="Error 404",
                        description="Warning channel not found. Please set it again using `[p]warnset channel`.",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=error_embed)
            else:
                error_embed = discord.Embed(
                    title="Error 404",
                    description="No warning channel has been set. Please set it using `[p]warnset channel`.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=error_embed)
        else:
            error_embed = discord.Embed(
                title="Error 404",
                description=f"Warning with ID {warning_id} not found.",
                color=discord.Color.red()
            )
            await ctx.send(embed=error_embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def topwarners(self, ctx):
        """Show the top 5 users who have issued the most warnings in the current server."""
        warnings_issued = await self.config.guild(ctx.guild).warnings_issued()
        sorted_users = sorted(warnings_issued.items(), key=lambda item: item[1], reverse=True)

        embed = discord.Embed(
            title="Top 5 Warners",
            color=discord.Color.gold()
        )

        if sorted_users:
            for rank, (user_id, count) in enumerate(sorted_users[:5], start=1):
                user = self.bot.get_user(int(user_id))
                embed.add_field(
                    name=f"{rank}. {user} (ID: {user_id})",
                    value=f"Warnings Issued: {count}",
                    inline=False
                )
        else:
            embed.add_field(name="No data available", value="No warnings have been issued yet.", inline=False)

        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def modwarns(self, ctx, moderator: discord.Member):
        """Show the number of warnings issued by a moderator and who they have warned in the current server."""
        mod_warnings = await self.config.guild(ctx.guild).mod_warnings()
        if str(moderator.id) in mod_warnings:
            warnings = mod_warnings[str(moderator.id)]
            embed = discord.Embed(
                title=f"Warnings Issued by {moderator}",
                color=discord.Color.blue()
            )
            embed.add_field(name="Total Warnings Issued", value=len(warnings), inline=False)

            for warning in warnings:
                warned_user = self.bot.get_user(warning["user"])
                timestamp = int(datetime.fromisoformat(warning['time']).timestamp())
                embed.add_field(
                    name=f"<:user:1268083437768671303> | User Warned: {warned_user} (ID: {warning['user']})",
                    value=f"<:reason:1268083436598591539> | Reason: {warning['reason']}\n<:time:1268083440864198676> | Time: <t:{timestamp}:F>\n<:channel:1268083439651913819> | Channel: <#{warning['channel']}>",
                    inline=False
                )
        else:
            embed = discord.Embed(
                title=f"{moderator} has not issued any warnings.",
                color=discord.Color.red()
            )

        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def adboard(self, ctx):
        """Show all users who have issued warnings and how many they have issued."""
        warnings_issued = await self.config.guild(ctx.guild).warnings_issued()
        sorted_users = sorted(warnings_issued.items(), key=lambda item: item[1], reverse=True)

        embed = discord.Embed(
            title="AdBoard - Warning Issuers",
            color=discord.Color.purple()
        )

        if sorted_users:
            for rank, (user_id, count) in enumerate(sorted_users, start=1):
                user = self.bot.get_user(int(user_id))
                embed.add_field(
                    name=f"{rank}. {user} (ID: {user_id})",
                    value=f"Warnings Issued: {count}",
                    inline=False
                )
        else:
            embed.add_field(name="No data available", value="No warnings have been issued yet.", inline=False)

        await ctx.send(embed=embed)

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
        """Show the current warning channel and thresholds."""
        channel_id = await self.config.guild(ctx.guild).warn_channel()
        tholds = await self.config.guild(ctx.guild).tholds()

        embed = discord.Embed(
            title="Warning System Configuration",
            color=discord.Color.blue()
        )

        if channel_id:
            channel = self.bot.get_channel(channel_id)
            embed.add_field(name="<:channel:1268083439651913819> | Current Warning Channel", value=channel.mention, inline=False)
        else:
            embed.add_field(name="<:channel:1268083439651913819> | Current Warning Channel", value="Not set", inline=False)

        if tholds:
            threshold_list = "\n".join([f"{threshold_id}: {threshold['count']} warnings -> {threshold['action']}" for threshold_id, threshold in tholds.items()])
            embed.add_field(name="Warning Thresholds", value=threshold_list, inline=False)
        else:
            embed.add_field(name="Warning Thresholds", value="No thresholds set", inline=False)

        await ctx.send(embed=embed)

    @warnset.command()
    async def threshold(self, ctx, warning_count: int, action: str):
        """Set an action for a specific warning count threshold."""
        valid_actions = ["kick", "ban", "timeout", "softban"]  # Add more actions as needed
        if action not in valid_actions:
            await ctx.send(f"Invalid action. Valid actions are: {', '.join(valid_actions)}")
            return

        tholds = await self.config.guild(ctx.guild).tholds()
        threshold_id = str(uuid.uuid4())
        tholds[threshold_id] = {
            "count": warning_count,
            "action": action
        }
        await self.config.guild(ctx.guild).tholds.set(tholds)
        await ctx.send(f"Set action '{action}' for reaching {warning_count} warnings.")

    @warnset.command()
    async def delthreshold(self, ctx, threshold_id: str):
        """Delete a specific warning count threshold by its UUID."""
        tholds = await self.config.guild(ctx.guild).tholds()
        if threshold_id in tholds:
            del tholds[threshold_id]
            await self.config.guild(ctx.guild).tholds.set(tholds)
            await ctx.send(f"Deleted threshold with ID {threshold_id}.")
        else:
            await ctx.send(f"No threshold set with ID {threshold_id}.")

    @warnset.command()
    async def softbanduration(self, ctx, days: int):
        """Set the duration (in days) for message deletion during a softban."""
        await self.config.guild(ctx.guild).softban_duration.set(days)
        await ctx.send(f"Softban message deletion duration set to {days} days.")

    @warnset.command()
    async def timeoutduration(self, ctx, minutes: int):
        """Set the duration (in minutes) for timeouts."""
        await self.config.guild(ctx.guild).timeout_duration.set(minutes)
        await ctx.send(f"Timeout duration set to {minutes} minutes.")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def adrace(self, ctx, duration: int):
        """Start an adwarn race that lasts for a configurable amount of time."""
        custom_emoji = "<a:winner:1269746569872412785>"  # Custom emoji

        join_end_time = discord.utils.utcnow() + timedelta(seconds=60)
        join_end_timestamp = int(join_end_time.timestamp())

        embed = discord.Embed(
            title="AdWarn Race Join",
            description=f"React with the custom emoji to join the AdWarn race! You have until <t:{join_end_timestamp}:R> to join.",
            color=discord.Color.gold()
        )
        join_message = await ctx.send(embed=embed)
        await join_message.add_reaction(custom_emoji)

        def check(reaction, user):
            return (
                str(reaction.emoji) == custom_emoji
                and reaction.message.id == join_message.id
                and user != self.bot.user
            )

        participants = []
        participants_mentions = ""

        # Countdown for 1 minute
        while discord.utils.utcnow() < join_end_time:
            try:
                remaining = (join_end_time - discord.utils.utcnow()).total_seconds()
                reaction, user = await self.bot.wait_for("reaction_add", timeout=remaining, check=check)
                if user not in participants:
                    participants.append(user)
                    participants_mentions = ", ".join(user.mention for user in participants)
                    embed.description = f"Participants: {participants_mentions}\nYou have until <t:{join_end_timestamp}:R> to join."
                    await join_message.edit(embed=embed)
            except asyncio.TimeoutError:
                break

        # Final update to the join message
        if participants:
            embed.description = f"Participants: {participants_mentions}\nTime's up! The race is starting now."
        else:
            embed.description = "No one joined the race. The race is cancelled."
        await join_message.edit(embed=embed)

        if not participants:
            return

        race_start_time = discord.utils.utcnow()
        race_end_time = race_start_time + timedelta(minutes=duration)

        embed = discord.Embed(
            title="AdWarn Race Started",
            color=discord.Color.gold()
        )
        embed.add_field(name="Starts", value=f"<t:{int(race_start_time.timestamp())}:R>", inline=True)
        embed.add_field(name="Ends", value=f"<t:{int(race_end_time.timestamp())}:R>", inline=True)
        embed.add_field(name="Participants", value=participants_mentions, inline=False)
        race_message = await ctx.send(embed=embed)

        await asyncio.sleep(duration * 60)

        results = {}
        for participant in participants:
            warnings = 0
            for channel in ctx.guild.text_channels:
                async for message in channel.history(limit=None):
                    if message.author == participant and "adwarn" in message.content:
                        warnings += 1
            results[participant] = warnings

        sorted_results = sorted(results.items(), key=lambda item: item[1], reverse=True)

        embed.title = "AdWarn Race Results"
        embed.description = f"The race lasted for {duration} minutes. Here are the results:"
        embed.clear_fields()

        for rank, (user, count) in enumerate(sorted_results, start=1):
            embed.add_field(name=f"{rank}. {user}", value=f"Warnings: {count}", inline=False)

        await race_message.edit(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def weeklystats(self, ctx):
        """Send an embed with the weekly AdWarn stats sorted by per-issuer."""
        weekly_stats = await self.config.guild(ctx.guild).weekly_stats()
        sorted_stats = sorted(weekly_stats.items(), key=lambda item: item[1], reverse=True)

        embed = discord.Embed(
            title="Weekly AdWarn Stats",
            color=discord.Color.blue()
        )

        if sorted_stats:
            for rank, (user_id, count) in enumerate(sorted_stats, start=1):
                user = self.bot.get_user(int(user_id))
                embed.add_field(
                    name=f"{rank}. {user} (ID: {user_id})",
                    value=f"Warnings Issued: {count}",
                    inline=False
                )
        else:
            embed.add_field(name="No data available", value="No warnings have been issued this week.", inline=False)

        await ctx.send(embed=embed)

        # Reset weekly stats
        await self.config.guild(ctx.guild).weekly_stats.set({})

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def monthlystats(self, ctx):
        """Send an embed with the monthly AdWarn stats sorted by per-issuer."""
        monthly_stats = await self.config.guild(ctx.guild).monthly_stats()
        sorted_stats = sorted(monthly_stats.items(), key=lambda item: item[1], reverse=True)

        embed = discord.Embed(
            title="Monthly AdWarn Stats",
            color=discord.Color.blue()
        )

        if sorted_stats:
            for rank, (user_id, count) in enumerate(sorted_stats, start=1):
                user = self.bot.get_user(int(user_id))
                embed.add_field(
                    name=f"{rank}. {user} (ID: {user_id})",
                    value=f"Warnings Issued: {count}",
                    inline=False
                )
        else:
            embed.add_field(name="No data available", value="No warnings have been issued this month.", inline=False)

        await ctx.send(embed=embed)

        # Reset monthly stats
        await self.config.guild(ctx.guild).monthly_stats.set({})

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listener to update weekly and monthly stats."""
        if message.author.bot:
            return

        if message.content.startswith("!adwarn"):
            author_id = str(message.author.id)
            weekly_stats = await self.config.guild(message.guild).weekly_stats()
            monthly_stats = await self.config.guild(message.guild).monthly_stats()

            if author_id not in weekly_stats:
                weekly_stats[author_id] = 0
            if author_id not in monthly_stats:
                monthly_stats[author_id] = 0

            weekly_stats[author_id] += 1
            monthly_stats[author_id] += 1

            await self.config.guild(message.guild).weekly_stats.set(weekly_stats)
            await self.config.guild(message.guild).monthly_stats.set(monthly_stats)
