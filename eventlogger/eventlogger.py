from redbot.core import commands, Config
from redbot.core.bot import Red
import discord
import logging

# Set up logging
log = logging.getLogger("red.EventLogger")

class EventLogger(commands.Cog):
    """Cog to log various Discord events"""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "channels": {},
            "command_log_channel": None
        }
        self.config.register_guild(**default_guild)

    async def log_event(self, guild: discord.Guild, event: str, details: dict):
        channels = await self.config.guild(guild).channels()
        channel_id = channels.get(event)
        if channel_id:
            channel = guild.get_channel(channel_id)
            if channel:
                embed = discord.Embed(title=f"Event: {event}", color=discord.Color.blue())
                for key, value in details.items():
                    embed.add_field(name=key, value=value, inline=False)
                await channel.send(embed=embed)
        log.info(f"Event: {event} | Guild: {guild.name} ({guild.id}) | Details: {details}")

    async def log_command(self, ctx, command_name: str):
        command_log_channel_id = await self.config.guild(ctx.guild).command_log_channel()
        if command_log_channel_id:
            channel = ctx.guild.get_channel(command_log_channel_id)
            if channel:
                embed = discord.Embed(title="Command Executed", color=discord.Color.green())
                embed.add_field(name="Command", value=command_name, inline=False)
                embed.add_field(name="User", value=f"{ctx.author} ({ctx.author.id})", inline=False)
                embed.add_field(name="Channel", value=f"{ctx.channel} ({ctx.channel.id})", inline=False)
                embed.add_field(name="Guild", value=f"{ctx.guild.name} ({ctx.guild.id})", inline=False)
                await channel.send(embed=embed)
        log.info(f"Command: {command_name} | User: {ctx.author} ({ctx.author.id}) | Channel: {ctx.channel} ({ctx.channel.id}) | Guild: {ctx.guild.name} ({ctx.guild.id})")

    # Commands to configure logging channels
    @commands.group()
    async def setlog(self, ctx):
        """Configure logging channels for events"""
        log.info(f"Command 'setlog' invoked by {ctx.author} in guild {ctx.guild.name} ({ctx.guild.id})")
        pass

    @setlog.command()
    async def event(self, ctx, event: str, channel: discord.TextChannel):
        """Set the logging channel for a specific event"""
        async with self.config.guild(ctx.guild).channels() as channels:
            channels[event] = channel.id
        await ctx.send(f"Logging channel for {event} set to {channel.mention}")
        log.info(f"Logging channel for event '{event}' set to {channel.name} ({channel.id}) in guild {ctx.guild.name} ({ctx.guild.id}) by {ctx.author}")

    @setlog.command()
    async def category(self, ctx, category: str, channel: discord.TextChannel):
        """Set the logging channel for a category of events"""
        event_categories = {
            "app": ["integration_create", "integration_delete", "integration_update"],
            "channel": ["guild_channel_create", "guild_channel_delete", "guild_channel_update", "guild_channel_pins_update", "guild_channel_name_update", "guild_channel_topic_update", "guild_channel_nsfw_update", "guild_channel_parent_update", "guild_channel_permissions_update", "guild_channel_type_update", "guild_channel_bitrate_update", "guild_channel_user_limit_update", "guild_channel_slowmode_update", "guild_channel_rtc_region_update", "guild_channel_video_quality_update", "guild_channel_default_archive_duration_update", "guild_channel_default_thread_slowmode_update", "guild_channel_default_reaction_emoji_update", "guild_channel_default_sort_order_update", "guild_channel_forum_tags_update", "guild_channel_forum_layout_update"],
            "voice": ["voice_state_update"],
            "automod": ["automod_rule_create", "automod_rule_delete", "automod_rule_update"],
            "emoji": ["guild_emojis_update", "guild_emoji_create", "guild_emoji_delete", "guild_emoji_update"],
            "event": ["scheduled_event_create", "scheduled_event_delete", "scheduled_event_update", "scheduled_event_user_add", "scheduled_event_user_remove"],
            "invite": ["invite_create", "invite_delete"],
            "message": ["message_delete", "bulk_message_delete", "message_edit"],
            "role": ["guild_role_create", "guild_role_delete", "guild_role_update"],
            "ban": ["member_ban", "member_unban"],
            "user": ["user_update", "member_update", "user_roles_update", "user_roles_add", "user_roles_remove", "user_avatar_update", "user_timeout", "user_timeout_remove"],
            "webhook": ["webhook_update", "webhook_create", "webhook_delete"],
            "thread": ["thread_create", "thread_delete", "thread_update", "thread_member_join", "thread_member_remove"],
            "sticker": ["guild_sticker_create", "guild_sticker_delete", "guild_sticker_update"],
            "soundboard": ["soundboard_sound_upload", "soundboard_sound_name_update", "soundboard_sound_volume_update", "soundboard_sound_emoji_update", "soundboard_sound_delete"],
            "server": ["guild_update", "guild_afk_channel_update", "guild_afk_timeout_update", "guild_banner_update", "guild_message_notifications_update", "guild_discovery_splash_update", "guild_explicit_content_filter_update", "guild_features_update", "guild_icon_update", "guild_mfa_level_update", "guild_name_update", "guild_description_update", "guild_partner_status_update", "guild_boost_level_update", "guild_boost_progress_bar_update", "guild_public_updates_channel_update", "guild_rules_channel_update", "guild_splash_update", "guild_system_channel_update", "guild_vanity_url_update", "guild_verification_level_update", "guild_verified_update", "guild_widget_update", "guild_preferred_locale_update"],
            "onboarding": ["guild_onboarding_toggle", "guild_onboarding_channels_update", "guild_onboarding_question_add", "guild_onboarding_question_remove", "guild_onboarding_update"],
            "moderation": ["ban_add", "ban_remove", "case_delete", "case_update", "kick_add", "kick_remove", "mute_add", "mute_remove", "warn_add", "warn_remove", "report_create", "reports_ignore", "reports_accept", "user_note_add", "user_note_remove"]
        }
        events = event_categories.get(category)
        if not events:
            await ctx.send(f"Invalid category: {category}")
            log.warning(f"Invalid category '{category}' specified by {ctx.author} in guild {ctx.guild.name} ({ctx.guild.id})")
            return
        async with self.config.guild(ctx.guild).channels() as channels:
            for event in events:
                channels[event] = channel.id
        await ctx.send(f"Logging channel for category {category} set to {channel.mention}")
        log.info(f"Logging channel for category '{category}' set to {channel.name} ({channel.id}) in guild {ctx.guild.name} ({ctx.guild.id}) by {ctx.author}")

    @setlog.command()
    async def commandlog(self, ctx, channel: discord.TextChannel):
        """Set the logging channel for commands"""
        await self.config.guild(ctx.guild).command_log_channel.set(channel.id)
        await ctx.send(f"Command logging channel set to {channel.mention}")
        log.info(f"Command logging channel set to {channel.name} ({channel.id}) in guild {ctx.guild.name} ({ctx.guild.id}) by {ctx.author}")

    @setlog.command()
    async def view(self, ctx):
        """View the current logging channels"""
        channels = await self.config.guild(ctx.guild).channels()
        command_log_channel_id = await self.config.guild(ctx.guild).command_log_channel()
        if not channels and not command_log_channel_id:
            await ctx.send("No logging channels set.")
            log.info(f"No logging channels set in guild {ctx.guild.name} ({ctx.guild.id})")
            return
        message = "Current logging channels:\n"
        for event, channel_id in channels.items():
            channel = ctx.guild.get_channel(channel_id)
            if channel:
                message += f"{event}: {channel.mention}\n"
        if command_log_channel_id:
            command_log_channel = ctx.guild.get_channel(command_log_channel_id)
            if command_log_channel:
                message += f"Command Log: {command_log_channel.mention}\n"
        await ctx.send(message)
        log.info(f"Current logging channels viewed by {ctx.author} in guild {ctx.guild.name} ({ctx.guild.id})")

    @setlog.command()
    async def categories(self, ctx):
        """View the event categories and their events"""
        event_categories = {
            "app": ["integration_create", "integration_delete", "integration_update"],
            "channel": ["guild_channel_create", "guild_channel_delete", "guild_channel_update", "guild_channel_pins_update", "guild_channel_name_update", "guild_channel_topic_update", "guild_channel_nsfw_update", "guild_channel_parent_update", "guild_channel_permissions_update", "guild_channel_type_update", "guild_channel_bitrate_update", "guild_channel_user_limit_update", "guild_channel_slowmode_update", "guild_channel_rtc_region_update", "guild_channel_video_quality_update", "guild_channel_default_archive_duration_update", "guild_channel_default_thread_slowmode_update", "guild_channel_default_reaction_emoji_update", "guild_channel_default_sort_order_update", "guild_channel_forum_tags_update", "guild_channel_forum_layout_update"],
            "voice": ["voice_state_update"],
            "automod": ["automod_rule_create", "automod_rule_delete", "automod_rule_update"],
            "emoji": ["guild_emojis_update", "guild_emoji_create", "guild_emoji_delete", "guild_emoji_update"],
            "event": ["scheduled_event_create", "scheduled_event_delete", "scheduled_event_update", "scheduled_event_user_add", "scheduled_event_user_remove"],
            "invite": ["invite_create", "invite_delete"],
            "message": ["message_delete", "bulk_message_delete", "message_edit"],
            "role": ["guild_role_create", "guild_role_delete", "guild_role_update"],
            "ban": ["member_ban", "member_unban"],
            "user": ["user_update", "member_update", "user_roles_update", "user_roles_add", "user_roles_remove", "user_avatar_update", "user_timeout", "user_timeout_remove"],
            "webhook": ["webhook_update", "webhook_create", "webhook_delete"],
            "thread": ["thread_create", "thread_delete", "thread_update", "thread_member_join", "thread_member_remove"],
            "sticker": ["guild_sticker_create", "guild_sticker_delete", "guild_sticker_update"],
            "soundboard": ["soundboard_sound_upload", "soundboard_sound_name_update", "soundboard_sound_volume_update", "soundboard_sound_emoji_update", "soundboard_sound_delete"],
            "server": ["guild_update", "guild_afk_channel_update", "guild_afk_timeout_update", "guild_banner_update", "guild_message_notifications_update", "guild_discovery_splash_update", "guild_explicit_content_filter_update", "guild_features_update", "guild_icon_update", "guild_mfa_level_update", "guild_name_update", "guild_description_update", "guild_partner_status_update", "guild_boost_level_update", "guild_boost_progress_bar_update", "guild_public_updates_channel_update", "guild_rules_channel_update", "guild_splash_update", "guild_system_channel_update", "guild_vanity_url_update", "guild_verification_level_update", "guild_verified_update", "guild_widget_update", "guild_preferred_locale_update"],
            "onboarding": ["guild_onboarding_toggle", "guild_onboarding_channels_update", "guild_onboarding_question_add", "guild_onboarding_question_remove", "guild_onboarding_update"],
            "moderation": ["ban_add", "ban_remove", "case_delete", "case_update", "kick_add", "kick_remove", "mute_add", "mute_remove", "warn_add", "warn_remove", "report_create", "reports_ignore", "reports_accept", "user_note_add", "user_note_remove"]
        }
        embed = discord.Embed(title="Event Categories and Their Events", color=discord.Color.blue())
        for category, events in event_categories.items():
            embed.add_field(name=category.capitalize(), value="\n".join(events), inline=False)
        await ctx.send(embed=embed)
        log.info(f"Event categories viewed by {ctx.author} in guild {ctx.guild.name} ({ctx.guild.id})")

    # Event listeners
    @commands.Cog.listener()
    async def on_integration_create(self, integration: discord.Integration):
        details = {
            "Integration": integration.name,
            "Integration ID": integration.id,
            "Guild": integration.guild.name,
            "Guild ID": integration.guild.id
        }
        await self.log_event(integration.guild, "integration_create", details)

    @commands.Cog.listener()
    async def on_integration_delete(self, integration: discord.Integration):
        details = {
            "Integration": integration.name,
            "Integration ID": integration.id,
            "Guild": integration.guild.name,
            "Guild ID": integration.guild.id
        }
        await self.log_event(integration.guild, "integration_delete", details)

    @commands.Cog.listener()
    async def on_integration_update(self, integration: discord.Integration):
        details = {
            "Integration": integration.name,
            "Integration ID": integration.id,
            "Guild": integration.guild.name,
            "Guild ID": integration.guild.id
        }
        await self.log_event(integration.guild, "integration_update", details)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        details = {
            "Channel": channel.name,
            "Channel ID": channel.id,
            "Channel Type": str(channel.type),
            "Guild": channel.guild.name,
            "Guild ID": channel.guild.id,
            "Creator": channel.guild.me.name if channel.guild.me else "N/A",
            "Creator ID": channel.guild.me.id if channel.guild.me else "N/A"
        }
        await self.log_event(channel.guild, "guild_channel_create", details)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        details = {
            "Channel": channel.name,
            "Channel ID": channel.id,
            "Channel Type": str(channel.type),
            "Guild": channel.guild.name,
            "Guild ID": channel.guild.id,
            "Deleter": channel.guild.me.name if channel.guild.me else "N/A",
            "Deleter ID": channel.guild.me.id if channel.guild.me else "N/A"
        }
        await self.log_event(channel.guild, "guild_channel_delete", details)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        details = {
            "Before Channel": before.name,
            "After Channel": after.name,
            "Channel ID": before.id,
            "Guild": before.guild.name,
            "Guild ID": before.guild.id,
            "Updater": before.guild.me.name if before.guild.me else "N/A",
            "Updater ID": before.guild.me.id if before.guild.me else "N/A"
        }
        await self.log_event(before.guild, "guild_channel_update", details)

    @commands.Cog.listener()
    async def on_guild_channel_pins_update(self, channel: discord.abc.GuildChannel, last_pin: discord.Message):
        details = {
            "Channel": channel.name,
            "Channel ID": channel.id,
            "Guild": channel.guild.name,
            "Guild ID": channel.guild.id,
            "Last Pin": last_pin.content if last_pin else "None",
            "Pinner": last_pin.author.name if last_pin else "N/A",
            "Pinner ID": last_pin.author.id if last_pin else "N/A"
        }
        await self.log_event(channel.guild, "guild_channel_pins_update", details)

    @commands.Cog.listener()
    async def on_guild_channel_name_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        details = {
            "Before Name": before.name,
            "After Name": after.name,
            "Channel ID": before.id,
            "Guild": before.guild.name,
            "Guild ID": before.guild.id,
            "Updater": before.guild.me.name if before.guild.me else "N/A",
            "Updater ID": before.guild.me.id if before.guild.me else "N/A"
        }
        await self.log_event(before.guild, "guild_channel_name_update", details)

    @commands.Cog.listener()
    async def on_guild_channel_topic_update(self, before: discord.TextChannel, after: discord.TextChannel):
        details = {
            "Before Topic": before.topic,
            "After Topic": after.topic,
            "Channel ID": before.id,
            "Guild": before.guild.name,
            "Guild ID": before.guild.id,
            "Updater": before.guild.me.name if before.guild.me else "N/A",
            "Updater ID": before.guild.me.id if before.guild.me else "N/A"
        }
        await self.log_event(before.guild, "guild_channel_topic_update", details)

    @commands.Cog.listener()
    async def on_guild_channel_nsfw_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        details = {
            "Before NSFW": before.is_nsfw(),
            "After NSFW": after.is_nsfw(),
            "Channel ID": before.id,
            "Guild": before.guild.name,
            "Guild ID": before.guild.id,
            "Updater": before.guild.me.name if before.guild.me else "N/A",
            "Updater ID": before.guild.me.id if before.guild.me else "N/A"
        }
        await self.log_event(before.guild, "guild_channel_nsfw_update", details)

    @commands.Cog.listener()
    async def on_guild_channel_parent_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        details = {
            "Before Parent": before.category.name if before.category else "None",
            "After Parent": after.category.name if after.category else "None",
            "Channel ID": before.id,
            "Guild": before.guild.name,
            "Guild ID": before.guild.id,
            "Updater": before.guild.me.name if before.guild.me else "N/A",
            "Updater ID": before.guild.me.id if before.guild.me else "N/A"
        }
        await self.log_event(before.guild, "guild_channel_parent_update", details)

    @commands.Cog.listener()
    async def on_guild_channel_permissions_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        details = {
            "Before Permissions": str(before.overwrites),
            "After Permissions": str(after.overwrites),
            "Channel ID": before.id,
            "Guild": before.guild.name,
            "Guild ID": before.guild.id,
            "Updater": before.guild.me.name if before.guild.me else "N/A",
            "Updater ID": before.guild.me.id if before.guild.me else "N/A"
        }
        await self.log_event(before.guild, "guild_channel_permissions_update", details)

    @commands.Cog.listener()
    async def on_guild_channel_type_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        details = {
            "Before Type": str(before.type),
            "After Type": str(after.type),
            "Channel ID": before.id,
            "Guild": before.guild.name,
            "Guild ID": before.guild.id,
            "Updater": before.guild.me.name if before.guild.me else "N/A",
            "Updater ID": before.guild.me.id if before.guild.me else "N/A"
        }
        await self.log_event(before.guild, "guild_channel_type_update", details)

    @commands.Cog.listener()
    async def on_guild_channel_bitrate_update(self, before: discord.VoiceChannel, after: discord.VoiceChannel):
        details = {
            "Before Bitrate": before.bitrate,
            "After Bitrate": after.bitrate,
            "Channel ID": before.id,
            "Guild": before.guild.name,
            "Guild ID": before.guild.id,
            "Updater": before.guild.me.name if before.guild.me else "N/A",
            "Updater ID": before.guild.me.id if before.guild.me else "N/A"
        }
        await self.log_event(before.guild, "guild_channel_bitrate_update", details)

    @commands.Cog.listener()
    async def on_guild_channel_user_limit_update(self, before: discord.VoiceChannel, after: discord.VoiceChannel):
        details = {
            "Before User Limit": before.user_limit,
            "After User Limit": after.user_limit,
            "Channel ID": before.id,
            "Guild": before.guild.name,
            "Guild ID": before.guild.id,
            "Updater": before.guild.me.name if before.guild.me else "N/A",
            "Updater ID": before.guild.me.id if before.guild.me else "N/A"
        }
        await self.log_event(before.guild, "guild_channel_user_limit_update", details)

    @commands.Cog.listener()
    async def on_guild_channel_slowmode_update(self, before: discord.TextChannel, after: discord.TextChannel):
        details = {
            "Before Slowmode": before.slowmode_delay,
            "After Slowmode": after.slowmode_delay,
            "Channel ID": before.id,
            "Guild": before.guild.name,
            "Guild ID": before.guild.id,
            "Updater": before.guild.me.name if before.guild.me else "N/A",
            "Updater ID": before.guild.me.id if before.guild.me else "N/A"
        }
        await self.log_event(before.guild, "guild_channel_slowmode_update", details)

    @commands.Cog.listener()
    async def on_guild_channel_rtc_region_update(self, before: discord.VoiceChannel, after: discord.VoiceChannel):
        details = {
            "Before RTC Region": before.rtc_region,
            "After RTC Region": after.rtc_region,
            "Channel ID": before.id,
            "Guild": before.guild.name,
            "Guild ID": before.guild.id,
            "Updater": before.guild.me.name if before.guild.me else "N/A",
            "Updater ID": before.guild.me.id if before.guild.me else "N/A"
        }
        await self.log_event(before.guild, "guild_channel_rtc_region_update", details)

    @commands.Cog.listener()
    async def on_guild_channel_video_quality_update(self, before: discord.VoiceChannel, after: discord.VoiceChannel):
        details = {
            "Before Video Quality": before.video_quality_mode,
            "After Video Quality": after.video_quality_mode,
            "Channel ID": before.id,
            "Guild": before.guild.name,
            "Guild ID": before.guild.id,
            "Updater": before.guild.me.name if before.guild.me else "N/A",
            "Updater ID": before.guild.me.id if before.guild.me else "N/A"
        }
        await self.log_event(before.guild, "guild_channel_video_quality_update", details)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        details = {
            "Member": member.name,
            "Member ID": member.id,
            "Guild": member.guild.name,
            "Guild ID": member.guild.id,
            "Before Channel": str(before.channel) if before.channel else "None",
            "After Channel": str(after.channel) if after.channel else "None",
            "Before Mute": before.mute,
            "After Mute": after.mute,
            "Before Deaf": before.deaf,
            "After Deaf": after.deaf
        }
        await self.log_event(member.guild, "voice_state_update", details)

    @commands.Cog.listener()
    async def on_automod_rule_create(self, rule: discord.AutoModRule):
        details = {
            "Rule": rule.name,
            "Rule ID": rule.id,
            "Guild": rule.guild.name,
            "Guild ID": rule.guild.id,
            "Creator": rule.creator.name if rule.creator else "N/A",
            "Creator ID": rule.creator.id if rule.creator else "N/A"
        }
        await self.log_event(rule.guild, "automod_rule_create", details)

    @commands.Cog.listener()
    async def on_automod_rule_delete(self, rule: discord.AutoModRule):
        details = {
            "Rule": rule.name,
            "Rule ID": rule.id,
            "Guild": rule.guild.name,
            "Guild ID": rule.guild.id,
            "Deleter": rule.creator.name if rule.creator else "N/A",
            "Deleter ID": rule.creator.id if rule.creator else "N/A"
        }
        await self.log_event(rule.guild, "automod_rule_delete", details)

    @commands.Cog.listener()
    async def on_automod_rule_update(self, before: discord.AutoModRule, after: discord.AutoModRule):
        details = {
            "Before Rule": before.name,
            "After Rule": after.name,
            "Rule ID": before.id,
            "Guild": before.guild.name,
            "Guild ID": before.guild.id,
            "Updater": before.creator.name if before.creator else "N/A",
            "Updater ID": before.creator.id if before.creator else "N/A"
        }
        await self.log_event(before.guild, "automod_rule_update", details)

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild: discord.Guild, before: list[discord.Emoji], after: list[discord.Emoji]):
        details = {
            "Guild": guild.name,
            "Guild ID": guild.id,
            "Before Emojis": ", ".join([emoji.name for emoji in before]),
            "After Emojis": ", ".join([emoji.name for emoji in after])
        }
        await self.log_event(guild, "guild_emojis_update", details)

    @commands.Cog.listener()
    async def on_guild_emoji_create(self, emoji: discord.Emoji):
        details = {
            "Emoji": emoji.name,
            "Emoji ID": emoji.id,
            "Guild": emoji.guild.name,
            "Guild ID": emoji.guild.id,
            "Creator": emoji.user.name if emoji.user else "N/A",
            "Creator ID": emoji.user.id if emoji.user else "N/A"
        }
        await self.log_event(emoji.guild, "guild_emoji_create", details)

    @commands.Cog.listener()
    async def on_guild_emoji_delete(self, emoji: discord.Emoji):
        details = {
            "Emoji": emoji.name,
            "Emoji ID": emoji.id,
            "Guild": emoji.guild.name,
            "Guild ID": emoji.guild.id,
            "Deleter": emoji.user.name if emoji.user else "N/A",
            "Deleter ID": emoji.user.id if emoji.user else "N/A"
        }
        await self.log_event(emoji.guild, "guild_emoji_delete", details)

    @commands.Cog.listener()
    async def on_guild_emoji_update(self, before: discord.Emoji, after: discord.Emoji):
        details = {
            "Before Emoji": before.name,
            "After Emoji": after.name,
            "Emoji ID": before.id,
            "Guild": before.guild.name,
            "Guild ID": before.guild.id,
            "Updater": before.user.name if before.user else "N/A",
            "Updater ID": before.user.id if before.user else "N/A"
        }
        await self.log_event(before.guild, "guild_emoji_update", details)

    @commands.Cog.listener()
    async def on_scheduled_event_create(self, event: discord.ScheduledEvent):
        details = {
            "Event": event.name,
            "Event ID": event.id,
            "Guild": event.guild.name,
            "Guild ID": event.guild.id,
            "Creator": event.creator.name if event.creator else "N/A",
            "Creator ID": event.creator.id if event.creator else "N/A"
        }
        await self.log_event(event.guild, "scheduled_event_create", details)

    @commands.Cog.listener()
    async def on_scheduled_event_delete(self, event: discord.ScheduledEvent):
        details = {
            "Event": event.name,
            "Event ID": event.id,
            "Guild": event.guild.name,
            "Guild ID": event.guild.id,
            "Deleter": event.creator.name if event.creator else "N/A",
            "Deleter ID": event.creator.id if event.creator else "N/A"
        }
        await self.log_event(event.guild, "scheduled_event_delete", details)

    @commands.Cog.listener()
    async def on_scheduled_event_update(self, before: discord.ScheduledEvent, after: discord.ScheduledEvent):
        details = {
            "Before Event": before.name,
            "After Event": after.name,
            "Event ID": before.id,
            "Guild": before.guild.name,
            "Guild ID": before.guild.id,
            "Updater": before.creator.name if before.creator else "N/A",
            "Updater ID": before.creator.id if before.creator else "N/A"
        }
        await self.log_event(before.guild, "scheduled_event_update", details)

    @commands.Cog.listener()
    async def on_scheduled_event_user_add(self, event: discord.ScheduledEvent, user: discord.User):
        details = {
            "User": user.name,
            "User ID": user.id,
            "Event": event.name,
            "Event ID": event.id,
            "Guild": event.guild.name,
            "Guild ID": event.guild.id
        }
        await self.log_event(event.guild, "scheduled_event_user_add", details)

    @commands.Cog.listener()
    async def on_scheduled_event_user_remove(self, event: discord.ScheduledEvent, user: discord.User):
        details = {
            "User": user.name,
            "User ID": user.id,
            "Event": event.name,
            "Event ID": event.id,
            "Guild": event.guild.name,
            "Guild ID": event.guild.id
        }
        await self.log_event(event.guild, "scheduled_event_user_remove", details)

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        details = {
            "Invite URL": invite.url,
            "Invite ID": invite.id,
            "Guild": invite.guild.name,
            "Guild ID": invite.guild.id,
            "Channel": invite.channel.name,
            "Channel ID": invite.channel.id,
            "Creator": invite.inviter.name if invite.inviter else "N/A",
            "Creator ID": invite.inviter.id if invite.inviter else "N/A"
        }
        await self.log_event(invite.guild, "invite_create", details)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        details = {
            "Invite URL": invite.url,
            "Invite ID": invite.id,
            "Guild": invite.guild.name,
            "Guild ID": invite.guild.id,
            "Channel": invite.channel.name,
            "Channel ID": invite.channel.id,
            "Deleter": invite.inviter.name if invite.inviter else "N/A",
            "Deleter ID": invite.inviter.id if invite.inviter else "N/A"
        }
        await self.log_event(invite.guild, "invite_delete", details)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        details = {
            "Message Content": message.content,
            "Message ID": message.id,
            "Author": message.author.name,
            "Author ID": message.author.id,
            "Channel": message.channel.name,
            "Channel ID": message.channel.id,
            "Guild": message.guild.name,
            "Guild ID": message.guild.id
        }
        await self.log_event(message.guild, "message_delete", details)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages: list[discord.Message]):
        details = {
            "Message Count": len(messages),
            "Channel": messages[0].channel.name,
            "Channel ID": messages[0].channel.id,
            "Guild": messages[0].guild.name,
            "Guild ID": messages[0].guild.id,
            "Messages": ", ".join([message.content for message in messages])
        }
        await self.log_event(messages[0].guild, "bulk_message_delete", details)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        details = {
            "Before Content": before.content,
            "After Content": after.content,
            "Message ID": before.id,
            "Author": before.author.name,
            "Author ID": before.author.id,
            "Channel": before.channel.name,
            "Channel ID": before.channel.id,
            "Guild": before.guild.name,
            "Guild ID": before.guild.id
        }
        await self.log_event(before.guild, "message_edit", details)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        details = {
            "Role": role.name,
            "Role ID": role.id,
            "Guild": role.guild.name,
            "Guild ID": role.guild.id,
            "Creator": role.guild.me.name if role.guild.me else "N/A",
            "Creator ID": role.guild.me.id if role.guild.me else "N/A"
        }
        await self.log_event(role.guild, "guild_role_create", details)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        details = {
            "Role": role.name,
            "Role ID": role.id,
            "Guild": role.guild.name,
            "Guild ID": role.guild.id,
            "Deleter": role.guild.me.name if role.guild.me else "N/A",
            "Deleter ID": role.guild.me.id if role.guild.me else "N/A"
        }
        await self.log_event(role.guild, "guild_role_delete", details)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        details = {
            "Before Role": before.name,
            "After Role": after.name,
            "Role ID": before.id,
            "Guild": before.guild.name,
            "Guild ID": before.guild.id,
            "Updater": before.guild.me.name if before.guild.me else "N/A",
            "Updater ID": before.guild.me.id if before.guild.me else "N/A"
        }
        await self.log_event(before.guild, "guild_role_update", details)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        details = {
            "User": user.name,
            "User ID": user.id,
            "Guild": guild.name,
            "Guild ID": guild.id,
            "Banner": guild.me.name if guild.me else "N/A",
            "Banner ID": guild.me.id if guild.me else "N/A"
        }
        await self.log_event(guild, "member_ban", details)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        details = {
            "User": user.name,
            "User ID": user.id,
            "Guild": guild.name,
            "Guild ID": guild.id,
            "Unbanner": guild.me.name if guild.me else "N/A",
            "Unbanner ID": guild.me.id if guild.me else "N/A"
        }
        await self.log_event(guild, "member_unban", details)

    @commands.Cog.listener()
    async def on_user_update(self, before: discord.User, after: discord.User):
        details = {
            "Before Name": before.name,
            "After Name": after.name,
            "User ID": before.id,
            "Before Discriminator": before.discriminator,
            "After Discriminator": after.discriminator,
            "Before Avatar": str(before.avatar_url),
            "After Avatar": str(after.avatar_url),
            "Before Bot": before.bot,
            "After Bot": after.bot,
            "Before System": before.system,
            "After System": after.system
        }
        await self.log_event(before.guild, "user_update", details)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        details = {
            "Before Name": before.name,
            "After Name": after.name,
            "Member ID": before.id,
            "Guild": before.guild.name,
            "Guild ID": before.guild.id,
            "Before Nick": before.nick,
            "After Nick": after.nick,
            "Before Roles": ", ".join([role.name for role in before.roles]),
            "After Roles": ", ".join([role.name for role in after.roles]),
            "Before Status": str(before.status),
            "After Status": str(after.status),
            "Before Activity": str(before.activity),
            "After Activity": str(after.activity)
        }
        await self.log_event(before.guild, "member_update", details)

    @commands.Cog.listener()
    async def on_user_roles_update(self, before: discord.Member, after: discord.Member):
        details = {
            "Member": before.name,
            "Member ID": before.id,
            "Before Roles": ", ".join([role.name for role in before.roles]),
            "After Roles": ", ".join([role.name for role in after.roles]),
            "Guild": before.guild.name,
            "Guild ID": before.guild.id
        }
        await self.log_event(before.guild, "user_roles_update", details)

    @commands.Cog.listener()
    async def on_user_roles_add(self, member: discord.Member, role: discord.Role):
        details = {
            "Member": member.name,
            "Member ID": member.id,
            "Role Added": role.name,
            "Role ID": role.id,
            "Guild": member.guild.name,
            "Guild ID": member.guild.id,
            "Adder": member.guild.me.name if member.guild.me else "N/A",
            "Adder ID": member.guild.me.id if member.guild.me else "N/A"
        }
        await self.log_event(member.guild, "user_roles_add", details)

    @commands.Cog.listener()
    async def on_user_roles_remove(self, member: discord.Member, role: discord.Role):
        details = {
            "Member": member.name,
            "Member ID": member.id,
            "Role Removed": role.name,
            "Role ID": role.id,
            "Guild": member.guild.name,
            "Guild ID": member.guild.id,
            "Remover": member.guild.me.name if member.guild.me else "N/A",
            "Remover ID": member.guild.me.id if member.guild.me else "N/A"
        }
        await self.log_event(member.guild, "user_roles_remove", details)

    @commands.Cog.listener()
    async def on_user_avatar_update(self, before: discord.User, after: discord.User):
        details = {
            "User": before.name,
            "User ID": before.id,
            "Before Avatar": str(before.avatar_url),
            "After Avatar": str(after.avatar_url),
            "Guild": before.guild.name if before.guild else "DM",
            "Guild ID": before.guild.id if before.guild else "DM"
        }
        await self.log_event(before.guild, "user_avatar_update", details)

    @commands.Cog.listener()
    async def on_user_timeout(self, member: discord.Member):
        details = {
            "Member": member.name,
            "Member ID": member.id,
            "Guild": member.guild.name,
            "Guild ID": member.guild.id,
            "Timeout By": member.guild.me.name if member.guild.me else "N/A",
            "Timeout By ID": member.guild.me.id if member.guild.me else "N/A"
        }
        await self.log_event(member.guild, "user_timeout", details)

    @commands.Cog.listener()
    async def on_user_timeout_remove(self, member: discord.Member):
        details = {
            "Member": member.name,
            "Member ID": member.id,
            "Guild": member.guild.name,
            "Guild ID": member.guild.id,
            "Timeout Removed By": member.guild.me.name if member.guild.me else "N/A",
            "Timeout Removed By ID": member.guild.me.id if member.guild.me else "N/A"
        }
        await self.log_event(member.guild, "user_timeout_remove", details)

    @commands.Cog.listener()
    async def on_webhook_update(self, channel: discord.abc.GuildChannel):
        details = {
            "Channel": channel.name,
            "Channel ID": channel.id,
            "Guild": channel.guild.name,
            "Guild ID": channel.guild.id,
            "Updater": channel.guild.me.name if channel.guild.me else "N/A",
            "Updater ID": channel.guild.me.id if channel.guild.me else "N/A"
        }
        await self.log_event(channel.guild, "webhook_update", details)

    @commands.Cog.listener()
    async def on_webhook_create(self, webhook: discord.Webhook):
        details = {
            "Webhook": webhook.name,
            "Webhook ID": webhook.id,
            "Channel": webhook.channel.name,
            "Channel ID": webhook.channel.id,
            "Guild": webhook.guild.name,
            "Guild ID": webhook.guild.id,
            "Creator": webhook.user.name if webhook.user else "N/A",
            "Creator ID": webhook.user.id if webhook.user else "N/A"
        }
        await self.log_event(webhook.guild, "webhook_create", details)

    @commands.Cog.listener()
    async def on_webhook_delete(self, webhook: discord.Webhook):
        details = {
            "Webhook": webhook.name,
            "Webhook ID": webhook.id,
            "Channel": webhook.channel.name,
            "Channel ID": webhook.channel.id,
            "Guild": webhook.guild.name,
            "Guild ID": webhook.guild.id,
            "Deleter": webhook.user.name if webhook.user else "N/A",
            "Deleter ID": webhook.user.id if webhook.user else "N/A"
        }
        await self.log_event(webhook.guild, "webhook_delete", details)

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        details = {
            "Thread": thread.name,
            "Thread ID": thread.id,
            "Guild": thread.guild.name,
            "Guild ID": thread.guild.id,
            "Creator": thread.owner.name if thread.owner else "N/A",
            "Creator ID": thread.owner.id if thread.owner else "N/A"
        }
        await self.log_event(thread.guild, "thread_create", details)

    @commands.Cog.listener()
    async def on_thread_delete(self, thread: discord.Thread):
        details = {
            "Thread": thread.name,
            "Thread ID": thread.id,
            "Guild": thread.guild.name,
            "Guild ID": thread.guild.id,
            "Deleter": thread.owner.name if thread.owner else "N/A",
            "Deleter ID": thread.owner.id if thread.owner else "N/A"
        }
        await self.log_event(thread.guild, "thread_delete", details)

    @commands.Cog.listener()
    async def on_thread_update(self, before: discord.Thread, after: discord.Thread):
        details = {
            "Before Thread": before.name,
            "After Thread": after.name,
            "Thread ID": before.id,
            "Guild": before.guild.name,
            "Guild ID": before.guild.id,
            "Updater": before.owner.name if before.owner else "N/A",
            "Updater ID": before.owner.id if before.owner else "N/A"
        }
        await self.log_event(before.guild, "thread_update", details)

    @commands.Cog.listener()
    async def on_thread_member_join(self, member: discord.ThreadMember):
        details = {
            "Member": member.name,
            "Member ID": member.id,
            "Thread": member.thread.name,
            "Thread ID": member.thread.id,
            "Guild": member.guild.name,
            "Guild ID": member.guild.id
        }
        await self.log_event(member.guild, "thread_member_join", details)

    @commands.Cog.listener()
    async def on_thread_member_remove(self, member: discord.ThreadMember):
        details = {
            "Member": member.name,
            "Member ID": member.id,
            "Thread": member.thread.name,
            "Thread ID": member.thread.id,
            "Guild": member.guild.name,
            "Guild ID": member.guild.id
        }
        await self.log_event(member.guild, "thread_member_remove", details)

    @commands.Cog.listener()
    async def on_guild_sticker_create(self, sticker: discord.Sticker):
        details = {
            "Sticker": sticker.name,
            "Sticker ID": sticker.id,
            "Guild": sticker.guild.name,
            "Guild ID": sticker.guild.id,
            "Creator": sticker.user.name if sticker.user else "N/A",
            "Creator ID": sticker.user.id if sticker.user else "N/A"
        }
        await self.log_event(sticker.guild, "guild_sticker_create", details)

    @commands.Cog.listener()
    async def on_guild_sticker_delete(self, sticker: discord.Sticker):
        details = {
            "Sticker": sticker.name,
            "Sticker ID": sticker.id,
            "Guild": sticker.guild.name,
            "Guild ID": sticker.guild.id,
            "Deleter": sticker.user.name if sticker.user else "N/A",
            "Deleter ID": sticker.user.id if sticker.user else "N/A"
        }
        await self.log_event(sticker.guild, "guild_sticker_delete", details)

    @commands.Cog.listener()
    async def on_guild_sticker_update(self, before: discord.Sticker, after: discord.Sticker):
        details = {
            "Before Sticker": before.name,
            "After Sticker": after.name,
            "Sticker ID": before.id,
            "Guild": before.guild.name,
            "Guild ID": before.guild.id,
            "Updater": before.user.name if before.user else "N/A",
            "Updater ID": before.user.id if before.user else "N/A"
        }
        await self.log_event(before.guild, "guild_sticker_update", details)

    @commands.Cog.listener()
    async def on_soundboard_sound_upload(self, sound):
        details = {
            "Sound": sound.name,
            "Sound ID": sound.id,
            "Guild": sound.guild.name,
            "Guild ID": sound.guild.id,
            "Uploader": sound.user.name if sound.user else "N/A",
            "Uploader ID": sound.user.id if sound.user else "N/A"
        }
        await self.log_event(sound.guild, "soundboard_sound_upload", details)

    @commands.Cog.listener()
    async def on_soundboard_sound_name_update(self, before, after):
        details = {
            "Before Sound": before.name,
            "After Sound": after.name,
            "Sound ID": before.id,
            "Guild": before.guild.name,
            "Guild ID": before.guild.id,
            "Updater": before.user.name if before.user else "N/A",
            "Updater ID": before.user.id if before.user else "N/A"
        }
        await self.log_event(before.guild, "soundboard_sound_name_update", details)

    @commands.Cog.listener()
    async def on_soundboard_sound_volume_update(self, before, after):
        details = {
            "Before Volume": before.volume,
            "After Volume": after.volume,
            "Sound ID": before.id,
            "Guild": before.guild.name,
            "Guild ID": before.guild.id,
            "Updater": before.user.name if before.user else "N/A",
            "Updater ID": before.user.id if before.user else "N/A"
        }
        await self.log_event(before.guild, "soundboard_sound_volume_update", details)

    @commands.Cog.listener()
    async def on_soundboard_sound_emoji_update(self, before, after):
        details = {
            "Before Emoji": before.emoji,
            "After Emoji": after.emoji,
            "Sound ID": before.id,
            "Guild": before.guild.name,
            "Guild ID": before.guild.id,
            "Updater": before.user.name if before.user else "N/A",
            "Updater ID": before.user.id if before.user else "N/A"
        }
        await self.log_event(before.guild, "soundboard_sound_emoji_update", details)

    @commands.Cog.listener()
    async def on_soundboard_sound_delete(self, sound):
        details = {
            "Sound": sound.name,
            "Sound ID": sound.id,
            "Guild": sound.guild.name,
            "Guild ID": sound.guild.id,
            "Deleter": sound.user.name if sound.user else "N/A",
            "Deleter ID": sound.user.id if sound.user else "N/A"
        }
        await self.log_event(sound.guild, "soundboard_sound_delete", details)

    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        details = {
            "Before Name": before.name,
            "After Name": after.name,
            "Guild ID": before.id,
            "Before Description": before.description,
            "After Description": after.description,
            "Before Verification Level": str(before.verification_level),
            "After Verification Level": str(after.verification_level),
            "Before Default Message Notifications": str(before.default_notifications),
            "After Default Message Notifications": str(after.default_notifications),
            "Before Explicit Content Filter": str(before.explicit_content_filter),
            "After Explicit Content Filter": str(after.explicit_content_filter),
            "Before MFA Level": str(before.mfa_level),
            "After MFA Level": str(after.mfa_level),
            "Before System Channel": str(before.system_channel),
            "After System Channel": str(after.system_channel),
            "Before Rules Channel": str(before.rules_channel),
            "After Rules Channel": str(after.rules_channel),
            "Before Public Updates Channel": str(before.public_updates_channel),
            "After Public Updates Channel": str(after.public_updates_channel),
            "Before Preferred Locale": before.preferred_locale,
            "After Preferred Locale": after.preferred_locale,
            "Before AFK Channel": str(before.afk_channel),
            "After AFK Channel": str(after.afk_channel),
            "Before AFK Timeout": before.afk_timeout,
            "After AFK Timeout": after.afk_timeout,
            "Before Banner": str(before.banner),
            "After Banner": str(after.banner),
            "Before Splash": str(before.splash),
            "After Splash": str(after.splash),
            "Before Icon": str(before.icon),
            "After Icon": str(after.icon),
            "Before Vanity URL Code": before.vanity_url_code,
            "After Vanity URL Code": after.vanity_url_code,
            "Before Features": ", ".join(before.features),
            "After Features": ", ".join(after.features),
            "Before Boost Level": before.premium_tier,
            "After Boost Level": after.premium_tier,
            "Before Boost Progress Bar": before.premium_progress_bar_enabled,
            "After Boost Progress Bar": after.premium_progress_bar_enabled,
            "Updater": before.me.name if before.me else "N/A",
            "Updater ID": before.me.id if before.me else "N/A"
        }
        await self.log_event(before, "guild_update", details)

    @commands.Cog.listener()
    async def on_guild_afk_channel_update(self, before: discord.Guild, after: discord.Guild):
        details = {
            "Before AFK Channel": str(before.afk_channel),
            "After AFK Channel": str(after.afk_channel),
            "Guild ID": before.id,
            "Updater": before.me.name if before.me else "N/A",
            "Updater ID": before.me.id if before.me else "N/A"
        }
        await self.log_event(before, "guild_afk_channel_update", details)

    @commands.Cog.listener()
    async def on_guild_afk_timeout_update(self, before: discord.Guild, after: discord.Guild):
        details = {
            "Before AFK Timeout": before.afk_timeout,
            "After AFK Timeout": after.afk_timeout,
            "Guild ID": before.id,
            "Updater": before.me.name if before.me else "N/A",
            "Updater ID": before.me.id if before.me else "N/A"
        }
        await self.log_event(before, "guild_afk_timeout_update", details)

    @commands.Cog.listener()
    async def on_guild_banner_update(self, before: discord.Guild, after: discord.Guild):
        details = {
            "Before Banner": str(before.banner),
            "After Banner": str(after.banner),
            "Guild ID": before.id,
            "Updater": before.me.name if before.me else "N/A",
            "Updater ID": before.me.id if before.me else "N/A"
        }
        await self.log_event(before, "guild_banner_update", details)

    @commands.Cog.listener()
    async def on_guild_message_notifications_update(self, before: discord.Guild, after: discord.Guild):
        details = {
            "Before Default Notifications": str(before.default_notifications),
            "After Default Notifications": str(after.default_notifications),
            "Guild ID": before.id,
            "Updater": before.me.name if before.me else "N/A",
            "Updater ID": before.me.id if before.me else "N/A"
        }
        await self.log_event(before, "guild_message_notifications_update", details)

    @commands.Cog.listener()
    async def on_guild_discovery_splash_update(self, before: discord.Guild, after: discord.Guild):
        details = {
            "Before Discovery Splash": str(before.discovery_splash),
            "After Discovery Splash": str(after.discovery_splash),
            "Guild ID": before.id,
            "Updater": before.me.name if before.me else "N/A",
            "Updater ID": before.me.id if before.me else "N/A"
        }
        await self.log_event(before, "guild_discovery_splash_update", details)

    @commands.Cog.listener()
    async def on_guild_explicit_content_filter_update(self, before: discord.Guild, after: discord.Guild):
        details = {
            "Before Explicit Content Filter": str(before.explicit_content_filter),
            "After Explicit Content Filter": str(after.explicit_content_filter),
            "Guild ID": before.id,
            "Updater": before.me.name if before.me else "N/A",
            "Updater ID": before.me.id if before.me else "N/A"
        }
        await self.log_event(before, "guild_explicit_content_filter_update", details)

    @commands.Cog.listener()
    async def on_guild_features_update(self, before: discord.Guild, after: discord.Guild):
        details = {
            "Before Features": ", ".join(before.features),
            "After Features": ", ".join(after.features),
            "Guild ID": before.id,
            "Updater": before.me.name if before.me else "N/A",
            "Updater ID": before.me.id if before.me else "N/A"
        }
        await self.log_event(before, "guild_features_update", details)

    @commands.Cog.listener()
    async def on_guild_icon_update(self, before: discord.Guild, after: discord.Guild):
        details = {
            "Before Icon": str(before.icon),
            "After Icon": str(after.icon),
            "Guild ID": before.id,
            "Updater": before.me.name if before.me else "N/A",
            "Updater ID": before.me.id if before.me else "N/A"
        }
        await self.log_event(before, "guild_icon_update", details)

    @commands.Cog.listener()
    async def on_guild_mfa_level_update(self, before: discord.Guild, after: discord.Guild):
        details = {
            "Before MFA Level": str(before.mfa_level),
            "After MFA Level": str(after.mfa_level),
            "Guild ID": before.id,
            "Updater": before.me.name if before.me else "N/A",
            "Updater ID": before.me.id if before.me else "N/A"
        }
        await self.log_event(before, "guild_mfa_level_update", details)

    @commands.Cog.listener()
    async def on_guild_name_update(self, before: discord.Guild, after: discord.Guild):
        details = {
            "Before Name": before.name,
            "After Name": after.name,
            "Guild ID": before.id,
            "Updater": before.me.name if before.me else "N/A",
            "Updater ID": before.me.id if before.me else "N/A"
        }
        await self.log_event(before, "guild_name_update", details)

    @commands.Cog.listener()
    async def on_guild_description_update(self, before: discord.Guild, after: discord.Guild):
        details = {
            "Before Description": before.description,
            "After Description": after.description,
            "Guild ID": before.id,
            "Updater": before.me.name if before.me else "N/A",
            "Updater ID": before.me.id if before.me else "N/A"
        }
        await self.log_event(before, "guild_description_update", details)

    @commands.Cog.listener()
    async def on_guild_partner_status_update(self, before: discord.Guild, after: discord.Guild):
        details = {
            "Before Partner Status": before.partnered,
            "After Partner Status": after.partnered,
            "Guild ID": before.id,
            "Updater": before.me.name if before.me else "N/A",
            "Updater ID": before.me.id if before.me else "N/A"
        }
        await self.log_event(before, "guild_partner_status_update", details)

    @commands.Cog.listener()
    async def on_guild_boost_level_update(self, before: discord.Guild, after: discord.Guild):
        details = {
            "Before Boost Level": before.premium_tier,
            "After Boost Level": after.premium_tier,
            "Guild ID": before.id,
            "Updater": before.me.name if before.me else "N/A",
            "Updater ID": before.me.id if before.me else "N/A"
        }
        await self.log_event(before, "guild_boost_level_update", details)

    @commands.Cog.listener()
    async def on_guild_boost_progress_bar_update(self, before: discord.Guild, after: discord.Guild):
        details = {
            "Before Boost Progress Bar": before.premium_progress_bar_enabled,
            "After Boost Progress Bar": after.premium_progress_bar_enabled,
            "Guild ID": before.id,
            "Updater": before.me.name if before.me else "N/A",
            "Updater ID": before.me.id if before.me else "N/A"
        }
        await self.log_event(before, "guild_boost_progress_bar_update", details)

    @commands.Cog.listener()
    async def on_guild_public_updates_channel_update(self, before: discord.Guild, after: discord.Guild):
        details = {
            "Before Public Updates Channel": str(before.public_updates_channel),
            "After Public Updates Channel": str(after.public_updates_channel),
            "Guild ID": before.id,
            "Updater": before.me.name if before.me else "N/A",
            "Updater ID": before.me.id if before.me else "N/A"
        }
        await self.log_event(before, "guild_public_updates_channel_update", details)

    @commands.Cog.listener()
    async def on_guild_rules_channel_update(self, before: discord.Guild, after: discord.Guild):
        details = {
            "Before Rules Channel": str(before.rules_channel),
            "After Rules Channel": str(after.rules_channel),
            "Guild ID": before.id,
            "Updater": before.me.name if before.me else "N/A",
            "Updater ID": before.me.id if before.me else "N/A"
        }
        await self.log_event(before, "guild_rules_channel_update", details)

    @commands.Cog.listener()
    async def on_guild_splash_update(self, before: discord.Guild, after: discord.Guild):
        details = {
            "Before Splash": str(before.splash),
            "After Splash": str(after.splash),
            "Guild ID": before.id,
            "Updater": before.me.name if before.me else "N/A",
            "Updater ID": before.me.id if before.me else "N/A"
        }
        await self.log_event(before, "guild_splash_update", details)

    @commands.Cog.listener()
    async def on_guild_system_channel_update(self, before: discord.Guild, after: discord.Guild):
        details = {
            "Before System Channel": str(before.system_channel),
            "After System Channel": str(after.system_channel),
            "Guild ID": before.id,
            "Updater": before.me.name if before.me else "N/A",
            "Updater ID": before.me.id if before.me else "N/A"
        }
        await self.log_event(before, "guild_system_channel_update", details)

    @commands.Cog.listener()
    async def on_guild_vanity_url_update(self, before: discord.Guild, after: discord.Guild):
        details = {
            "Before Vanity URL Code": before.vanity_url_code,
            "After Vanity URL Code": after.vanity_url_code,
            "Guild ID": before.id,
            "Updater": before.me.name if before.me else "N/A",
            "Updater ID": before.me.id if before.me else "N/A"
        }
        await self.log_event(before, "guild_vanity_url_update", details)

    @commands.Cog.listener()
    async def on_guild_verification_level_update(self, before: discord.Guild, after: discord.Guild):
        details = {
            "Before Verification Level": str(before.verification_level),
            "After Verification Level": str(after.verification_level),
            "Guild ID": before.id,
            "Updater": before.me.name if before.me else "N/A",
            "Updater ID": before.me.id if before.me else "N/A"
        }
        await self.log_event(before, "guild_verification_level_update", details)

    @commands.Cog.listener()
    async def on_guild_verified_update(self, before: discord.Guild, after: discord.Guild):
        details = {
            "Before Verified Status": before.verified,
            "After Verified Status": after.verified,
            "Guild ID": before.id,
            "Updater": before.me.name if before.me else "N/A",
            "Updater ID": before.me.id if before.me else "N/A"
        }
        await self.log_event(before, "guild_verified_update", details)

    @commands.Cog.listener()
    async def on_guild_widget_update(self, before: discord.Guild, after: discord.Guild):
        details = {
            "Before Widget Enabled": before.widget_enabled,
            "After Widget Enabled": after.widget_enabled,
            "Guild ID": before.id,
            "Updater": before.me.name if before.me else "N/A",
            "Updater ID": before.me.id if before.me else "N/A"
        }
        await self.log_event(before, "guild_widget_update", details)

    @commands.Cog.listener()
    async def on_guild_preferred_locale_update(self, before: discord.Guild, after: discord.Guild):
        details = {
            "Before Preferred Locale": before.preferred_locale,
            "After Preferred Locale": after.preferred_locale,
            "Guild ID": before.id,
            "Updater": before.me.name if before.me else "N/A",
            "Updater ID": before.me.id if before.me else "N/A"
        }
        await self.log_event(before, "guild_preferred_locale_update", details)

    @commands.Cog.listener()
    async def on_guild_onboarding_toggle(self, guild: discord.Guild):
        details = {
            "Guild": guild.name,
            "Guild ID": guild.id,
            "Toggler": guild.me.name if guild.me else "N/A",
            "Toggler ID": guild.me.id if guild.me else "N/A"
        }
        await self.log_event(guild, "guild_onboarding_toggle", details)

    @commands.Cog.listener()
    async def on_guild_onboarding_channels_update(self, guild: discord.Guild, before, after):
        details = {
            "Guild": guild.name,
            "Guild ID": guild.id,
            "Before Channels": before,
            "After Channels": after,
            "Updater": guild.me.name if guild.me else "N/A",
            "Updater ID": guild.me.id if guild.me else "N/A"
        }
        await self.log_event(guild, "guild_onboarding_channels_update", details)

    @commands.Cog.listener()
    async def on_guild_onboarding_question_add(self, guild: discord.Guild, question):
        details = {
            "Guild": guild.name,
            "Guild ID": guild.id,
            "Question Added": question,
            "Adder": guild.me.name if guild.me else "N/A",
            "Adder ID": guild.me.id if guild.me else "N/A"
        }
        await self.log_event(guild, "guild_onboarding_question_add", details)

    @commands.Cog.listener()
    async def on_guild_onboarding_question_remove(self, guild: discord.Guild, question):
        details = {
            "Guild": guild.name,
            "Guild ID": guild.id,
            "Question Removed": question,
            "Remover": guild.me.name if guild.me else "N/A",
            "Remover ID": guild.me.id if guild.me else "N/A"
        }
        await self.log_event(guild, "guild_onboarding_question_remove", details)

    @commands.Cog.listener()
    async def on_guild_onboarding_update(self, guild: discord.Guild, before, after):
        details = {
            "Guild": guild.name,
            "Guild ID": guild.id,
            "Before": before,
            "After": after,
            "Updater": guild.me.name if guild.me else "N/A",
            "Updater ID": guild.me.id if guild.me else "N/A"
        }
        await self.log_event(guild, "guild_onboarding_update", details)

    @commands.Cog.listener()
    async def on_ban_add(self, guild: discord.Guild, user: discord.User):
        details = {
            "User": user.name,
            "User ID": user.id,
            "Guild": guild.name,
            "Guild ID": guild.id,
            "Banner": guild.me.name if guild.me else "N/A",
            "Banner ID": guild.me.id if guild.me else "N/A"
        }
        await self.log_event(guild, "ban_add", details)

    @commands.Cog.listener()
    async def on_ban_remove(self, guild: discord.Guild, user: discord.User):
        details = {
            "User": user.name,
            "User ID": user.id,
            "Guild": guild.name,
            "Guild ID": guild.id,
            "Unbanner": guild.me.name if guild.me else "N/A",
            "Unbanner ID": guild.me.id if guild.me else "N/A"
        }
        await self.log_event(guild, "ban_remove", details)

    @commands.Cog.listener()
    async def on_case_delete(self, case):
        details = {
            "Case ID": case.id,
            "Guild": case.guild.name,
            "Guild ID": case.guild.id,
            "Deleter": case.guild.me.name if case.guild.me else "N/A",
            "Deleter ID": case.guild.me.id if case.guild.me else "N/A"
        }
        await self.log_event(case.guild, "case_delete", details)

    @commands.Cog.listener()
    async def on_case_update(self, before, after):
        details = {
            "Before Case ID": before.id,
            "After Case ID": after.id,
            "Guild": before.guild.name,
            "Guild ID": before.guild.id,
            "Updater": before.guild.me.name if before.guild.me else "N/A",
            "Updater ID": before.guild.me.id if before.guild.me else "N/A"
        }
        await self.log_event(before.guild, "case_update", details)

    @commands.Cog.listener()
    async def on_kick_add(self, guild: discord.Guild, user: discord.User):
        details = {
            "User": user.name,
            "User ID": user.id,
            "Guild": guild.name,
            "Guild ID": guild.id,
            "Kicker": guild.me.name if guild.me else "N/A",
            "Kicker ID": guild.me.id if guild.me else "N/A"
        }
        await self.log_event(guild, "kick_add", details)

    @commands.Cog.listener()
    async def on_kick_remove(self, guild: discord.Guild, user: discord.User):
        details = {
            "User": user.name,
            "User ID": user.id,
            "Guild": guild.name,
            "Guild ID": guild.id,
            "Unkicker": guild.me.name if guild.me else "N/A",
            "Unkicker ID": guild.me.id if guild.me else "N/A"
        }
        await self.log_event(guild, "kick_remove", details)

    @commands.Cog.listener()
    async def on_mute_add(self, guild: discord.Guild, user: discord.User):
        details = {
            "User": user.name,
            "User ID": user.id,
            "Guild": guild.name,
            "Guild ID": guild.id,
            "Muter": guild.me.name if guild.me else "N/A",
            "Muter ID": guild.me.id if guild.me else "N/A"
        }
        await self.log_event(guild, "mute_add", details)

    @commands.Cog.listener()
    async def on_mute_remove(self, guild: discord.Guild, user: discord.User):
        details = {
            "User": user.name,
            "User ID": user.id,
            "Guild": guild.name,
            "Guild ID": guild.id,
            "Unmuter": guild.me.name if guild.me else "N/A",
            "Unmuter ID": guild.me.id if guild.me else "N/A"
        }
        await self.log_event(guild, "mute_remove", details)

    @commands.Cog.listener()
    async def on_warn_add(self, guild: discord.Guild, user: discord.User):
        details = {
            "User": user.name,
            "User ID": user.id,
            "Guild": guild.name,
            "Guild ID": guild.id,
            "Warner": guild.me.name if guild.me else "N/A",
            "Warner ID": guild.me.id if guild.me else "N/A"
        }
        await self.log_event(guild, "warn_add", details)

    @commands.Cog.listener()
    async def on_warn_remove(self, guild: discord.Guild, user: discord.User):
        details = {
            "User": user.name,
            "User ID": user.id,
            "Guild": guild.name,
            "Guild ID": guild.id,
            "Unwarner": guild.me.name if guild.me else "N/A",
            "Unwarner ID": guild.me.id if guild.me else "N/A"
        }
        await self.log_event(guild, "warn_remove", details)

    @commands.Cog.listener()
    async def on_report_create(self, report):
        details = {
            "Report ID": report.id,
            "Guild": report.guild.name,
            "Guild ID": report.guild.id,
            "Reporter": report.guild.me.name if report.guild.me else "N/A",
            "Reporter ID": report.guild.me.id if report.guild.me else "N/A"
        }
        await self.log_event(report.guild, "report_create", details)

    @commands.Cog.listener()
    async def on_reports_ignore(self, report):
        details = {
            "Report ID": report.id,
            "Guild": report.guild.name,
            "Guild ID": report.guild.id,
            "Ignorer": report.guild.me.name if report.guild.me else "N/A",
            "Ignorer ID": report.guild.me.id if report.guild.me else "N/A"
        }
        await self.log_event(report.guild, "reports_ignore", details)

    @commands.Cog.listener()
    async def on_reports_accept(self, report):
        details = {
            "Report ID": report.id,
            "Guild": report.guild.name,
            "Guild ID": report.guild.id,
            "Acceptor": report.guild.me.name if report.guild.me else "N/A",
            "Acceptor ID": report.guild.me.id if report.guild.me else "N/A"
        }
        await self.log_event(report.guild, "reports_accept", details)

    @commands.Cog.listener()
    async def on_user_note_add(self, user: discord.User, note):
        details = {
            "User": user.name,
            "User ID": user.id,
            "Note": note,
            "Guild": user.guild.name if user.guild else "DM",
            "Guild ID": user.guild.id if user.guild else "DM",
            "Adder": user.guild.me.name if user.guild.me else "N/A",
            "Adder ID": user.guild.me.id if user.guild.me else "N/A"
        }
        await self.log_event(user.guild, "user_note_add", details)

    @commands.Cog.listener()
    async def on_user_note_remove(self, user: discord.User, note):
        details = {
            "User": user.name,
            "User ID": user.id,
            "Note": note,
            "Guild": user.guild.name if user.guild else "DM",
            "Guild ID": user.guild.id if user.guild else "DM",
            "Remover": user.guild.me.name if user.guild.me else "N/A",
            "Remover ID": user.guild.me.id if user.guild.me else "N/A"
        }
        await self.log_event(user.guild, "user_note_remove", details)
