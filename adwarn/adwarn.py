import discord
from redbot.core import commands, Config, app_commands
from redbot.core.bot import Red
from datetime import timedelta, datetime
import re
import uuid
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AdWarn")

class WarningReasonModal(discord.ui.Modal):
    def __init__(self, bot, interaction, user, message):
        self.bot = bot
        self.interaction = interaction
        self.user = user
        self.message = message
        super().__init__(title="Provide Warning Reason")
        self.reason = discord.ui.TextInput(label="Reason", style=discord.TextStyle.long)
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        reason = self.reason.value
        guild = interaction.guild
        author = interaction.user
        channel = interaction.channel

        warn_channel_id = await self.bot.get_cog("AdWarn").config.guild(guild).warn_channel()
        recent_adwarn_channel_id = await self.bot.get_cog("AdWarn").config.guild(guild).recent_adwarn_channel()
        if warn_channel_id:
            warn_channel = self.bot.get_channel(warn_channel_id)
            if warn_channel:
                # Store the warning with a UUID
                warnings = await self.bot.get_cog("AdWarn").config.member(self.user).warnings()
                warning_time = discord.utils.utcnow()
                warning_id = str(uuid.uuid4())
                warnings.append({
                    "id": warning_id,
                    "reason": reason,
                    "moderator": author.id,
                    "time": warning_time.isoformat(),
                    "channel": channel.id
                })
                await self.bot.get_cog("AdWarn").config.member(self.user).warnings.set(warnings)
                # Increment the count of warnings issued by the moderator for the current server
                warnings_issued = await self.bot.get_cog("AdWarn").config.guild(guild).warnings_issued()
                if str(author.id) not in warnings_issued:
                    warnings_issued[str(author.id)] = 0
                warnings_issued[str(author.id)] += 1
                await self.bot.get_cog("AdWarn").config.guild(guild).warnings_issued.set(warnings_issued)
                # Store the details of the warning issued by the moderator
                mod_warnings = await self.bot.get_cog("AdWarn").config.guild(guild).mod_warnings()
                if str(author.id) not in mod_warnings:
                    mod_warnings[str(author.id)] = []
                mod_warnings[str(author.id)].append({
                    "user": self.user.id,
                    "reason": reason,
                    "time": warning_time.isoformat(),
                    "channel": channel.id
                })
                await self.bot.get_cog("AdWarn").config.guild(guild).mod_warnings.set(mod_warnings)
                # Create the embed message
                timestamp = int(warning_time.timestamp())
                embed = discord.Embed(title="New AdWarn", color=discord.Color.red())
                embed.add_field(name="User", value=self.user.mention, inline=True)
                embed.add_field(name="Warned In", value=channel.mention, inline=True)
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.add_field(name="Moderator", value=author.mention, inline=True)
                embed.add_field(name="Time", value=f"<t:{timestamp}:F>", inline=False)
                embed.set_footer(text=f"Total warnings: {len(warnings)}")
                # Send the embed to the specified warning channel
                await warn_channel.send(embed=embed)
                # Send plain text message to the warning channel
                await warn_channel.send(f"{self.user.mention}")
                # Update the recent adwarn voice channel
                if recent_adwarn_channel_id:
                    recent_adwarn_channel = self.bot.get_channel(recent_adwarn_channel_id)
                    if recent_adwarn_channel:
                        await recent_adwarn_channel.edit(name=f"Recent Adwarn: {self.user.name}")
                # Check thresholds and take action if necessary
                await self.bot.get_cog("AdWarn").check_thresholds(interaction, self.user, len(warnings))
                # Respond to the interaction to close the modal
                await interaction.response.send_message("Warning recorded successfully.", ephemeral=True)
                # Delete the message that triggered the modal
                try:
                    await self.message.delete()
                except discord.errors.NotFound:
                    logger.error("Failed to delete the message: Message not found")
            else:
                error_embed = discord.Embed(
                    title="Error 404",
                    description="Warning channel not found. Please set it again using `[p]warnset channel`.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
        else:
            error_embed = discord.Embed(
                title="Error 404",
                description="No warning channel has been set. Please set it using `[p]warnset channel`.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

@app_commands.context_menu(name="AdWarn")
async def adwarn_context_menu(interaction: discord.Interaction, message: discord.Message):
    user = message.author
    await interaction.response.send_modal(WarningReasonModal(interaction.client, interaction, user, message))

class AdWarn(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)  # Replace with a unique identifier
        self.config.register_guild(warn_channel=None, tholds={}, warnings_issued={}, mod_warnings={}, softban_duration=120, timeout_duration=120, recent_adwarn_channel=None)
        self.config.register_member(warnings=[], untimeout_time=None)
        self.race_start_time = None
        self.race_end_time = None
        self.race_participants = []

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.tree.add_command(adwarn_context_menu)
        await self.bot.tree.sync()

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
    async def adwarn(self, ctx: commands.Context, user: discord.Member, *, reason: str):
        guild = ctx.guild
        author = ctx.author
        channel = ctx.channel

        warn_channel_id = await self.config.guild(guild).warn_channel()
        recent_adwarn_channel_id = await self.config.guild(guild).recent_adwarn_channel()
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
                    "moderator": author.id,
                    "time": warning_time.isoformat(),
                    "channel": channel.id
                })
                await self.config.member(user).warnings.set(warnings)
                # Increment the count of warnings issued by the moderator for the current server
                warnings_issued = await self.config.guild(guild).warnings_issued()
                if str(author.id) not in warnings_issued:
                    warnings_issued[str(author.id)] = 0
                warnings_issued[str(author.id)] += 1
                await self.config.guild(guild).warnings_issued.set(warnings_issued)
                # Store the details of the warning issued by the moderator
                mod_warnings = await self.config.guild(guild).mod_warnings()
                if str(author.id) not in mod_warnings:
                    mod_warnings[str(author.id)] = []
                mod_warnings[str(author.id)].append({
                    "user": user.id,
                    "reason": reason,
                    "time": warning_time.isoformat(),
                    "channel": channel.id
                })
                await self.config.guild(guild).mod_warnings.set(mod_warnings)
                # Create the embed message
                timestamp = int(warning_time.timestamp())
                embed = discord.Embed(title="New AdWarn", color=discord.Color.red())
                embed.add_field(name="User", value=user.mention, inline=True)
                embed.add_field(name="Warned In", value=channel.mention, inline=True)
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.add_field(name="Moderator", value=author.mention, inline=True)
                embed.add_field(name="Time", value=f"<t:{timestamp}:F>", inline=False)
                embed.set_footer(text=f"Total warnings: {len(warnings)}")
                # Send the embed to the specified warning channel
                await warn_channel.send(embed=embed)
                # Send plain text message to the warning channel
                await warn_channel.send(f"{user.mention}")
                # Update the recent adwarn voice channel
                if recent_adwarn_channel_id:
                    recent_adwarn_channel = self.bot.get_channel(recent_adwarn_channel_id)
                    if recent_adwarn_channel:
                        await recent_adwarn_channel.edit(name=f"Recent Adwarn: {user.name}")
                # Check thresholds and take action if necessary
                await self.check_thresholds(ctx, user, len(warnings))
                # Respond to the interaction to close the modal
                await ctx.send("Warning recorded successfully.", delete_after=10)
                # Delete the command message after 30 seconds
                await asyncio.sleep(30)
                try:
                    await ctx.message.delete()
                except discord.errors.NotFound:
                    logger.error("Failed to delete the command message: Message not found")
            else:
                error_embed = discord.Embed(
                    title="Error 404",
                    description="Warning channel not found. Please set it again using `[p]warnset channel`.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=error_embed, delete_after=10)
        else:
            error_embed = discord.Embed(
                title="Error 404",
                description="No warning channel has been set. Please set it using `[p]warnset channel`.",
                color=discord.Color.red()
            )
            await ctx.send(embed=error_embed, delete_after=10)
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def removewarn(self, ctx, user: discord.Member, warning_id: str):
        warnings = await self.config.member(user).warnings()
        warning_to_remove = next((warning for warning in warnings if warning["id"] == warning_id), None)
        if warning_to_remove:
            warnings.remove(warning_to_remove)
            await self.config.member(user).warnings.set(warnings)
            warn_channel_id = await self.config.guild(ctx.guild).warn_channel()
            if warn_channel_id:
                warn_channel = self.bot.get_channel(warn_channel_id)
                if warn_channel:
                    embed = discord.Embed(title="AdWarn Removed", color=discord.Color.green())
                    embed.add_field(name="Warning", value=warning_to_remove["reason"], inline=False)
                    embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
                    embed.add_field(name="Removed Time", value=f"<t:{int(discord.utils.utcnow().timestamp())}:F>", inline=True)
                    embed.set_footer(text=f"Total warnings: {len(warnings)}")
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
        if ctx.message:
            try:
                await ctx.message.delete()
            except discord.errors.NotFound:
                logger.error("Failed to delete the command message: Message not found")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def warncount(self, ctx, user: discord.Member):
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
                value=f"Reason: {warning['reason']}\nModerator: <@{warning['moderator']}>\nTime: <t:{timestamp}:F>",
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clearwarns(self, ctx, user: discord.User):
        await self.config.member_from_ids(ctx.guild.id, user.id).warnings.set([])
        warn_channel_id = await self.config.guild(ctx.guild).warn_channel()
        if (warn_channel_id):
            warn_channel = self.bot.get_channel(warn_channel_id)
            if warn_channel:
                embed = discord.Embed(title="All Warnings Cleared", color=discord.Color.green())
                embed.add_field(name="User", value=user.mention, inline=True)
                embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
                embed.add_field(name="Cleared Time", value=f"<t:{int(discord.utils.utcnow().timestamp())}:F>", inline=True)
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
        warnings = await self.config.member(user).warnings()
        if warnings:
            removed_warning = warnings.pop()
            await self.config.member(user).warnings.set(warnings)
            warn_channel_id = await self.config.guild(ctx.guild).warn_channel()
            if warn_channel_id:
                warn_channel = self.bot.get_channel(warn_channel_id)
                if warn_channel:
                    embed = discord.Embed(title="Most Recent AdWarn Removed", color=discord.Color.green())
                    embed.add_field(name="Warning", value=removed_warning["reason"], inline=False)
                    embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
                    embed.add_field(name="Removed Time", value=f"<t:{int(discord.utils.utcnow().timestamp())}:F>", inline=True)
                    embed.set_footer(text=f"Total warnings: {len(warnings)}")
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
        warnings = await self.config.member(user).warnings()
        warning_to_edit = next((warning for warning in warnings if warning["id"] == warning_id), None)
        if warning_to_edit:
            warning_to_edit["reason"] = new_reason
            await self.config.member(user).warnings.set(warnings)
            warn_channel_id = await self.config.guild(ctx.guild).warn_channel()
            if warn_channel_id:
                warn_channel = self.bot.get_channel(warn_channel_id)
                if warn_channel:
                    embed = discord.Embed(title="AdWarn Edited", color=discord.Color.orange())
                    embed.add_field(name="Warning", value=new_reason, inline=False)
                    embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
                    embed.add_field(name="Edited Time", value=f"<t:{int(discord.utils.utcnow().timestamp())}:F>", inline=True)
                    embed.set_footer(text=f"Total warnings: {len(warnings)}")
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
                    name=f"User Warned: {warned_user} (ID: {warning['user']})",
                    value=f"Reason: {warning['reason']}\nTime: <t:{timestamp}:F>\nChannel: <#{warning['channel']}>",
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
        await self.config.guild(ctx.guild).warn_channel.set(channel.id)
        embed = discord.Embed(
            title="Warning Channel Set",
            description=f"Warning channel has been set to {channel.mention}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @warnset.command()
    async def recentadwarnchannel(self, ctx, channel: discord.VoiceChannel):
        await self.config.guild(ctx.guild).recent_adwarn_channel.set(channel.id)
        embed = discord.Embed(
            title="Recent Adwarn Channel Set",
            description=f"Recent adwarn channel has been set to {channel.mention}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @warnset.command()
    async def show(self, ctx):
        channel_id = await self.config.guild(ctx.guild).warn_channel()
        recent_adwarn_channel_id = await self.config.guild(ctx.guild).recent_adwarn_channel()
        tholds = await self.config.guild(ctx.guild).tholds()
        embed = discord.Embed(
            title="Warning System Configuration",
            color=discord.Color.blue()
        )
        if channel_id:
            channel = self.bot.get_channel(channel_id)
            embed.add_field(name="Current Warning Channel", value=channel.mention, inline=False)
        else:
            embed.add_field(name="Current Warning Channel", value="Not set", inline=False)
        if recent_adwarn_channel_id:
            recent_adwarn_channel = self.bot.get_channel(recent_adwarn_channel_id)
            embed.add_field(name="Recent Adwarn Channel", value=recent_adwarn_channel.mention, inline=False)
        else:
            embed.add_field(name="Recent Adwarn Channel", value="Not set", inline=False)
        if tholds:
            threshold_list = "\n".join([f"{threshold_id}: {threshold['count']} warnings -> {threshold['action']}" for threshold_id, threshold in tholds.items()])
            embed.add_field(name="Warning Thresholds", value=threshold_list, inline=False)
        else:
            embed.add_field(name="Warning Thresholds", value="No thresholds set", inline=False)
        await ctx.send(embed=embed)

    @warnset.command()
    async def threshold(self, ctx, warning_count: int, action: str):
        valid_actions = ["kick", "ban", "timeout", "softban"]
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
        tholds = await self.config.guild(ctx.guild).tholds()
        if threshold_id in tholds:
            del tholds[threshold_id]
            await self.config.guild(ctx.guild).tholds.set(tholds)
            await ctx.send(f"Deleted threshold with ID {threshold_id}.")
        else:
            await ctx.send(f"No threshold set with ID {threshold_id}.")

    @warnset.command()
    async def softbanduration(self, ctx, days: int):
        await self.config.guild(ctx.guild).softban_duration.set(days)
        await ctx.send(f"Softban message deletion duration set to {days} days.")

    @warnset.command()
    async def timeoutduration(self, ctx, minutes: int):
        await self.config.guild(ctx.guild).timeout_duration.set(minutes)
        await ctx.send(f"Timeout duration set to {minutes} minutes.")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def adrace(self, ctx, duration: int):
        custom_emoji = "<a:winner:1270075143049449522>"  # Custom emoji
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

        async def handle_reaction_remove(reaction, user):
            if str(reaction.emoji) == custom_emoji and reaction.message.id == join_message.id:
                if user in participants:
                    participants.remove(user)
                    participants_mentions = ", ".join(user.mention for user in participants)
                    embed.description = f"Participants: {participants_mentions}\nYou have until <t:{join_end_timestamp}:R> to join."
                    await join_message.edit(embed=embed)

        self.bot.add_listener(handle_reaction_remove, "on_reaction_remove")

        if participants:
            embed.description = f"Participants: {participants_mentions}\nTime's up! The race is starting now."
        else:
            embed.description = "No one joined the race. The race is cancelled."
        await join_message.clear_reactions()
        await join_message.edit(embed=embed)
        if not participants:
            self.bot.remove_listener(handle_reaction_remove, "on_reaction_remove")
            return

        self.race_start_time = discord.utils.utcnow()
        self.race_end_time = self.race_start_time + timedelta(minutes=duration)
        self.race_participants = [{"user": participant.id, "warnings": 0} for participant in participants]

        embed = discord.Embed(
            title="AdWarn Race Started",
            color=discord.Color.gold()
        )
        embed.add_field(name="Starts", value=f"<t:{int(self.race_start_time.timestamp())}:R>", inline=True)
        embed.add_field(name="Ends", value=f"<t:{int(self.race_end_time.timestamp())}:R>", inline=True)
        embed.add_field(name="Participants", value=participants_mentions, inline=False)
        race_message = await ctx.send(embed=embed)

        await asyncio.sleep(duration * 60)

        results = {}
        for participant in participants:
            warnings = await self.config.member(participant).warnings()
            warnings_during_race = [
                warning for warning in warnings
                if self.race_start_time <= datetime.fromisoformat(warning["time"]) <= self.race_end_time
            ]
            results[participant.id] = len(warnings_during_race)

        sorted_results = sorted(results.items(), key=lambda item: item[1], reverse=True)

        embed.title = "AdWarn Race Results"
        embed.description = f"The race lasted for {duration} minutes. Here are the results:"
        embed.clear_fields()
        for rank, (user_id, count) in enumerate(sorted_results, start=1):
            user = self.bot.get_user(user_id)
            embed.add_field(name=f"{rank}. {user}", value=f"Warnings: {count}", inline=False)

        await race_message.edit(embed=embed)
        self.bot.remove_listener(handle_reaction_remove, "on_reaction_remove")
