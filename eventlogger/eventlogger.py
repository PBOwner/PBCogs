from redbot.core import commands, Config
from redbot.core.bot import Red
import discord

class EventLogger(commands.Cog):
    """Cog to log various Discord events"""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "channels": {}
        }
        self.config.register_guild(**default_guild)

    async def log_event(self, guild: discord.Guild, event: str, message: str):
        channels = await self.config.guild(guild).channels()
        channel_id = channels.get(event)
        if channel_id:
            channel = guild.get_channel(channel_id)
            if channel:
                await channel.send(message)

    # Commands to configure logging channels
    @commands.group()
    async def setlog(self, ctx):
        """Configure logging channels for events"""
        pass

    @setlog.command()
    async def event(self, ctx, event: str, channel: discord.TextChannel):
        """Set the logging channel for a specific event"""
        async with self.config.guild(ctx.guild).channels() as channels:
            channels[event] = channel.id
        await ctx.send(f"Logging channel for {event} set to {channel.mention}")

    @setlog.command()
    async def category(self, ctx, category: str, channel: discord.TextChannel):
        """Set the logging channel for a category of events"""
        event_categories = {
            "app": ["integration_create", "integration_delete", "application_command_permissions_update"],
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
            return
        async with self.config.guild(ctx.guild).channels() as channels:
            for event in events:
                channels[event] = channel.id
        await ctx.send(f"Logging channel for category {category} set to {channel.mention}")

    @setlog.command()
    async def view(self, ctx):
        """View the current logging channels"""
        channels = await self.config.guild(ctx.guild).channels()
        if not channels:
            await ctx.send("No logging channels set.")
            return
        message = "Current logging channels:\n"
        for event, channel_id in channels.items():
            channel = ctx.guild.get_channel(channel_id)
            if channel:
                message += f"{event}: {channel.mention}\n"
        await ctx.send(message)

    @setlog.command()
    async def categories(self, ctx):
        """View the event categories and their events"""
        event_categories = {
            "app": ["integration_create", "integration_delete", "application_command_permissions_update"],
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

    # Event listeners
    @commands.Cog.listener()
    async def on_integration_create(self, integration: discord.Integration):
        await self.log_event(integration.guild, "integration_create", f"App added: {integration.name}")

    @commands.Cog.listener()
    async def on_integration_delete(self, integration: discord.Integration):
        await self.log_event(integration.guild, "integration_delete", f"App removed: {integration.name}")

    @commands.Cog.listener()
    async def on_application_command_permissions_update(self, permissions: discord.ApplicationCommandPermissions):
        guild = self.bot.get_guild(permissions.guild_id)
        await self.log_event(guild, "application_command_permissions_update", f"App command permissions updated: {permissions.id}")

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        await self.log_event(channel.guild, "guild_channel_create", f"Channel created: {channel.name}")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        await self.log_event(channel.guild, "guild_channel_delete", f"Channel deleted: {channel.name}")

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        await self.log_event(before.guild, "guild_channel_update", f"Channel updated: {before.name} -> {after.name}")

    @commands.Cog.listener()
    async def on_guild_channel_pins_update(self, channel: discord.abc.GuildChannel, last_pin: discord.Message):
        await self.log_event(channel.guild, "guild_channel_pins_update", f"Channel pins updated in: {channel.name}")

    @commands.Cog.listener()
    async def on_guild_channel_name_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        await self.log_event(before.guild, "guild_channel_name_update", f"Channel name updated: {before.name} -> {after.name}")

    @commands.Cog.listener()
    async def on_guild_channel_topic_update(self, before: discord.TextChannel, after: discord.TextChannel):
        await self.log_event(before.guild, "guild_channel_topic_update", f"Channel topic updated: {before.topic} -> {after.topic}")

    @commands.Cog.listener()
    async def on_guild_channel_nsfw_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        await self.log_event(before.guild, "guild_channel_nsfw_update", f"Channel NSFW updated: {before.is_nsfw()} -> {after.is_nsfw()}")

    @commands.Cog.listener()
    async def on_guild_channel_parent_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        await self.log_event(before.guild, "guild_channel_parent_update", f"Channel parent updated: {before.category} -> {after.category}")

    @commands.Cog.listener()
    async def on_guild_channel_permissions_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        await self.log_event(before.guild, "guild_channel_permissions_update", f"Channel permissions updated: {before.overwrites} -> {after.overwrites}")

    @commands.Cog.listener()
    async def on_guild_channel_type_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        await self.log_event(before.guild, "guild_channel_type_update", f"Channel type updated: {before.type} -> {after.type}")

    @commands.Cog.listener()
    async def on_guild_channel_bitrate_update(self, before: discord.VoiceChannel, after: discord.VoiceChannel):
        await self.log_event(before.guild, "guild_channel_bitrate_update", f"Channel bitrate updated: {before.bitrate} -> {after.bitrate}")

    @commands.Cog.listener()
    async def on_guild_channel_user_limit_update(self, before: discord.VoiceChannel, after: discord.VoiceChannel):
        await self.log_event(before.guild, "guild_channel_user_limit_update", f"Channel user limit updated: {before.user_limit} -> {after.user_limit}")

    @commands.Cog.listener()
    async def on_guild_channel_slowmode_update(self, before: discord.TextChannel, after: discord.TextChannel):
        await self.log_event(before.guild, "guild_channel_slowmode_update", f"Channel slow mode updated: {before.slowmode_delay} -> {after.slowmode_delay}")

    @commands.Cog.listener()
    async def on_guild_channel_rtc_region_update(self, before: discord.VoiceChannel, after: discord.VoiceChannel):
        await self.log_event(before.guild, "guild_channel_rtc_region_update", f"Channel RTC region updated: {before.rtc_region} -> {after.rtc_region}")

    @commands.Cog.listener()
    async def on_guild_channel_video_quality_update(self, before: discord.VoiceChannel, after: discord.VoiceChannel):
        await self.log_event(before.guild, "guild_channel_video_quality_update", f"Channel video quality updated: {before.video_quality_mode} -> {after.video_quality_mode}")

    @commands.Cog.listener()
    async def on_guild_channel_default_archive_duration_update(self, before: discord.Thread, after: discord.Thread):
        await self.log_event(before.guild, "guild_channel_default_archive_duration_update", f"Channel default archive duration updated: {before.auto_archive_duration} -> {after.auto_archive_duration}")

    @commands.Cog.listener()
    async def on_guild_channel_default_thread_slowmode_update(self, before: discord.Thread, after: discord.Thread):
        await self.log_event(before.guild, "guild_channel_default_thread_slowmode_update", f"Channel default thread slow mode updated: {before.slowmode_delay} -> {after.slowmode_delay}")

    @commands.Cog.listener()
    async def on_guild_channel_default_reaction_emoji_update(self, before: discord.ForumChannel, after: discord.ForumChannel):
        await self.log_event(before.guild, "guild_channel_default_reaction_emoji_update", f"Channel default reaction emoji updated: {before.default_reaction_emoji} -> {after.default_reaction_emoji}")

    @commands.Cog.listener()
    async def on_guild_channel_default_sort_order_update(self, before: discord.ForumChannel, after: discord.ForumChannel):
        await self.log_event(before.guild, "guild_channel_default_sort_order_update", f"Channel default sort order updated: {before.default_sort_order} -> {after.default_sort_order}")

    @commands.Cog.listener()
    async def on_guild_channel_forum_tags_update(self, before: discord.ForumChannel, after: discord.ForumChannel):
        await self.log_event(before.guild, "guild_channel_forum_tags_update", f"Channel forum tags updated: {before.available_tags} -> {after.available_tags}")

    @commands.Cog.listener()
    async def on_guild_channel_forum_layout_update(self, before: discord.ForumChannel, after: discord.ForumChannel):
        await self.log_event(before.guild, "guild_channel_forum_layout_update", f"Channel forum layout updated: {before.default_layout} -> {after.default_layout}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        await self.log_event(member.guild, "voice_state_update", f"Voice state updated for {member.name}")

    @commands.Cog.listener()
    async def on_automod_rule_create(self, rule: discord.AutoModRule):
        await self.log_event(rule.guild, "automod_rule_create", f"AutoMod rule created: {rule.name}")

    @commands.Cog.listener()
    async def on_automod_rule_delete(self, rule: discord.AutoModRule):
        await self.log_event(rule.guild, "automod_rule_delete", f"AutoMod rule deleted: {rule.name}")

    @commands.Cog.listener()
    async def on_automod_rule_update(self, before: discord.AutoModRule, after: discord.AutoModRule):
        await self.log_event(before.guild, "automod_rule_update", f"AutoMod rule updated: {before.name} -> {after.name}")

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild: discord.Guild, before: list[discord.Emoji], after: list[discord.Emoji]):
        await self.log_event(guild, "guild_emojis_update", f"Emojis updated in guild: {guild.name}")

    @commands.Cog.listener()
    async def on_guild_emoji_create(self, emoji: discord.Emoji):
        await self.log_event(emoji.guild, "guild_emoji_create", f"Emoji created: {emoji.name}")

    @commands.Cog.listener()
    async def on_guild_emoji_delete(self, emoji: discord.Emoji):
        await self.log_event(emoji.guild, "guild_emoji_delete", f"Emoji deleted: {emoji.name}")

    @commands.Cog.listener()
    async def on_guild_emoji_update(self, before: discord.Emoji, after: discord.Emoji):
        await self.log_event(before.guild, "guild_emoji_update", f"Emoji updated: {before.name} -> {after.name}")

    @commands.Cog.listener()
    async def on_scheduled_event_create(self, event: discord.ScheduledEvent):
        await self.log_event(event.guild, "scheduled_event_create", f"Event created: {event.name}")

    @commands.Cog.listener()
    async def on_scheduled_event_delete(self, event: discord.ScheduledEvent):
        await self.log_event(event.guild, "scheduled_event_delete", f"Event deleted: {event.name}")

    @commands.Cog.listener()
    async def on_scheduled_event_update(self, before: discord.ScheduledEvent, after: discord.ScheduledEvent):
        await self.log_event(before.guild, "scheduled_event_update", f"Event updated: {before.name} -> {after.name}")

    @commands.Cog.listener()
    async def on_scheduled_event_user_add(self, event: discord.ScheduledEvent, user: discord.User):
        await self.log_event(event.guild, "scheduled_event_user_add", f"User {user.name} subscribed to event: {event.name}")

    @commands.Cog.listener()
    async def on_scheduled_event_user_remove(self, event: discord.ScheduledEvent, user: discord.User):
        await self.log_event(event.guild, "scheduled_event_user_remove", f"User {user.name} unsubscribed from event: {event.name}")

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        await self.log_event(invite.guild, "invite_create", f"Invite created: {invite.url}")

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        await self.log_event(invite.guild, "invite_delete", f"Invite deleted: {invite.url}")

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        await self.log_event(message.guild, "message_delete", f"Message deleted: {message.content}")

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages: list[discord.Message]):
        await self.log_event(messages[0].guild, "bulk_message_delete", f"Bulk message delete: {len(messages)} messages")

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        await self.log_event(before.guild, "message_edit", f"Message edited: {before.content} -> {after.content}")

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        await self.log_event(role.guild, "guild_role_create", f"Role created: {role.name}")

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        await self.log_event(role.guild, "guild_role_delete", f"Role deleted: {role.name}")

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        await self.log_event(before.guild, "guild_role_update", f"Role updated: {before.name} -> {after.name}")

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        await self.log_event(guild, "member_ban", f"User banned: {user.name}")

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        await self.log_event(guild, "member_unban", f"User unbanned: {user.name}")

    @commands.Cog.listener()
    async def on_user_update(self, before: discord.User, after: discord.User):
        await self.log_event(after.guild, "user_update", f"User updated: {before.name} -> {after.name}")

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        await self.log_event(before.guild, "member_update", f"Member updated: {before.name} -> {after.name}")

    @commands.Cog.listener()
    async def on_user_roles_update(self, before: discord.Member, after: discord.Member):
        await self.log_event(before.guild, "user_roles_update", f"User roles updated for {before.name}")

    @commands.Cog.listener()
    async def on_user_roles_add(self, member: discord.Member, role: discord.Role):
        await self.log_event(member.guild, "user_roles_add", f"Role {role.name} added to user {member.name}")

    @commands.Cog.listener()
    async def on_user_roles_remove(self, member: discord.Member, role: discord.Role):
        await self.log_event(member.guild, "user_roles_remove", f"Role {role.name} removed from user {member.name}")

    @commands.Cog.listener()
    async def on_user_avatar_update(self, before: discord.User, after: discord.User):
        await self.log_event(before.guild, "user_avatar_update", f"User avatar updated for {before.name}")

    @commands.Cog.listener()
    async def on_user_timeout(self, member: discord.Member):
        await self.log_event(member.guild, "user_timeout", f"User timed out: {member.name}")

    @commands.Cog.listener()
    async def on_user_timeout_remove(self, member: discord.Member):
        await self.log_event(member.guild, "user_timeout_remove", f"User timeout removed: {member.name}")

    @commands.Cog.listener()
    async def on_webhook_update(self, channel: discord.abc.GuildChannel):
        await self.log_event(channel.guild, "webhook_update", f"Webhook updated in channel: {channel.name}")

    @commands.Cog.listener()
    async def on_webhook_create(self, webhook: discord.Webhook):
        await self.log_event(webhook.guild, "webhook_create", f"Webhook created: {webhook.name}")

    @commands.Cog.listener()
    async def on_webhook_delete(self, webhook: discord.Webhook):
        await self.log_event(webhook.guild, "webhook_delete", f"Webhook deleted: {webhook.name}")

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        await self.log_event(thread.guild, "thread_create", f"Thread created: {thread.name}")

    @commands.Cog.listener()
    async def on_thread_delete(self, thread: discord.Thread):
        await self.log_event(thread.guild, "thread_delete", f"Thread deleted: {thread.name}")

    @commands.Cog.listener()
    async def on_thread_update(self, before: discord.Thread, after: discord.Thread):
        await self.log_event(before.guild, "thread_update", f"Thread updated: {before.name} -> {after.name}")

    @commands.Cog.listener()
    async def on_thread_member_join(self, member: discord.ThreadMember):
        await self.log_event(member.guild, "thread_member_join", f"Member joined thread: {member.name}")

    @commands.Cog.listener()
    async def on_thread_member_remove(self, member: discord.ThreadMember):
        await self.log_event(member.guild, "thread_member_remove", f"Member left thread: {member.name}")

    @commands.Cog.listener()
    async def on_guild_sticker_create(self, sticker: discord.Sticker):
        await self.log_event(sticker.guild, "guild_sticker_create", f"Sticker created: {sticker.name}")

    @commands.Cog.listener()
    async def on_guild_sticker_delete(self, sticker: discord.Sticker):
        await self.log_event(sticker.guild, "guild_sticker_delete", f"Sticker deleted: {sticker.name}")

    @commands.Cog.listener()
    async def on_guild_sticker_update(self, before: discord.Sticker, after: discord.Sticker):
        await self.log_event(before.guild, "guild_sticker_update", f"Sticker updated: {before.name} -> {after.name}")

    @commands.Cog.listener()
    async def on_soundboard_sound_upload(self, sound):
        await self.log_event(sound.guild, "soundboard_sound_upload", f"Soundboard sound uploaded: {sound.name}")

    @commands.Cog.listener()
    async def on_soundboard_sound_name_update(self, before, after):
        await self.log_event(before.guild, "soundboard_sound_name_update", f"Soundboard sound name updated: {before.name} -> {after.name}")

    @commands.Cog.listener()
    async def on_soundboard_sound_volume_update(self, before, after):
        await self.log_event(before.guild, "soundboard_sound_volume_update", f"Soundboard sound volume updated: {before.volume} -> {after.volume}")

    @commands.Cog.listener()
    async def on_soundboard_sound_emoji_update(self, before, after):
        await self.log_event(before.guild, "soundboard_sound_emoji_update", f"Soundboard sound emoji updated: {before.emoji} -> {after.emoji}")

    @commands.Cog.listener()
    async def on_soundboard_sound_delete(self, sound):
        await self.log_event(sound.guild, "soundboard_sound_delete", f"Soundboard sound deleted: {sound.name}")

    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        await self.log_event(before, "guild_update", f"Guild updated: {before.name} -> {after.name}")

    @commands.Cog.listener()
    async def on_guild_afk_channel_update(self, before: discord.Guild, after: discord.Guild):
        await self.log_event(before, "guild_afk_channel_update", f"Guild AFK channel updated: {before.afk_channel} -> {after.afk_channel}")

    @commands.Cog.listener()
    async def on_guild_afk_timeout_update(self, before: discord.Guild, after: discord.Guild):
        await self.log_event(before, "guild_afk_timeout_update", f"Guild AFK timeout updated: {before.afk_timeout} -> {after.afk_timeout}")

    @commands.Cog.listener()
    async def on_guild_banner_update(self, before: discord.Guild, after: discord.Guild):
        await self.log_event(before, "guild_banner_update", f"Guild banner updated: {before.banner} -> {after.banner}")

    @commands.Cog.listener()
    async def on_guild_message_notifications_update(self, before: discord.Guild, after: discord.Guild):
        await self.log_event(before, "guild_message_notifications_update", f"Guild message notifications updated: {before.default_notifications} -> {after.default_notifications}")

    @commands.Cog.listener()
    async def on_guild_discovery_splash_update(self, before: discord.Guild, after: discord.Guild):
        await self.log_event(before, "guild_discovery_splash_update", f"Guild discovery splash updated: {before.discovery_splash} -> {after.discovery_splash}")

    @commands.Cog.listener()
    async def on_guild_explicit_content_filter_update(self, before: discord.Guild, after: discord.Guild):
        await self.log_event(before, "guild_explicit_content_filter_update", f"Guild explicit content filter updated: {before.explicit_content_filter} -> {after.explicit_content_filter}")

    @commands.Cog.listener()
    async def on_guild_features_update(self, before: discord.Guild, after: discord.Guild):
        await self.log_event(before, "guild_features_update", f"Guild features updated: {before.features} -> {after.features}")

    @commands.Cog.listener()
    async def on_guild_icon_update(self, before: discord.Guild, after: discord.Guild):
        await self.log_event(before, "guild_icon_update", f"Guild icon updated: {before.icon} -> {after.icon}")

    @commands.Cog.listener()
    async def on_guild_mfa_level_update(self, before: discord.Guild, after: discord.Guild):
        await self.log_event(before, "guild_mfa_level_update", f"Guild MFA level updated: {before.mfa_level} -> {after.mfa_level}")

    @commands.Cog.listener()
    async def on_guild_name_update(self, before: discord.Guild, after: discord.Guild):
        await self.log_event(before, "guild_name_update", f"Guild name updated: {before.name} -> {after.name}")

    @commands.Cog.listener()
    async def on_guild_description_update(self, before: discord.Guild, after: discord.Guild):
        await self.log_event(before, "guild_description_update", f"Guild description updated: {before.description} -> {after.description}")

    @commands.Cog.listener()
    async def on_guild_partner_status_update(self, before: discord.Guild, after: discord.Guild):
        await self.log_event(before, "guild_partner_status_update", f"Guild partner status updated: {before.partnered} -> {after.partnered}")

    @commands.Cog.listener()
    async def on_guild_boost_level_update(self, before: discord.Guild, after: discord.Guild):
        await self.log_event(before, "guild_boost_level_update", f"Guild boost level updated: {before.premium_tier} -> {after.premium_tier}")

    @commands.Cog.listener()
    async def on_guild_boost_progress_bar_update(self, before: discord.Guild, after: discord.Guild):
        await self.log_event(before, "guild_boost_progress_bar_update", f"Guild boost progress bar updated: {before.premium_progress_bar_enabled} -> {after.premium_progress_bar_enabled}")

    @commands.Cog.listener()
    async def on_guild_public_updates_channel_update(self, before: discord.Guild, after: discord.Guild):
        await self.log_event(before, "guild_public_updates_channel_update", f"Guild public updates channel updated: {before.public_updates_channel} -> {after.public_updates_channel}")

    @commands.Cog.listener()
    async def on_guild_rules_channel_update(self, before: discord.Guild, after: discord.Guild):
        await self.log_event(before, "guild_rules_channel_update", f"Guild rules channel updated: {before.rules_channel} -> {after.rules_channel}")

    @commands.Cog.listener()
    async def on_guild_splash_update(self, before: discord.Guild, after: discord.Guild):
        await self.log_event(before, "guild_splash_update", f"Guild splash updated: {before.splash} -> {after.splash}")

    @commands.Cog.listener()
    async def on_guild_system_channel_update(self, before: discord.Guild, after: discord.Guild):
        await self.log_event(before, "guild_system_channel_update", f"Guild system channel updated: {before.system_channel} -> {after.system_channel}")

    @commands.Cog.listener()
    async def on_guild_vanity_url_update(self, before: discord.Guild, after: discord.Guild):
        await self.log_event(before, "guild_vanity_url_update", f"Guild vanity URL updated: {before.vanity_url_code} -> {after.vanity_url_code}")

    @commands.Cog.listener()
    async def on_guild_verification_level_update(self, before: discord.Guild, after: discord.Guild):
        await self.log_event(before, "guild_verification_level_update", f"Guild verification level updated: {before.verification_level} -> {after.verification_level}")

    @commands.Cog.listener()
    async def on_guild_verified_update(self, before: discord.Guild, after: discord.Guild):
        await self.log_event(before, "guild_verified_update", f"Guild verified status updated: {before.verified} -> {after.verified}")

    @commands.Cog.listener()
    async def on_guild_widget_update(self, before: discord.Guild, after: discord.Guild):
        await self.log_event(before, "guild_widget_update", f"Guild widget updated: {before.widget_enabled} -> {after.widget_enabled}")

    @commands.Cog.listener()
    async def on_guild_preferred_locale_update(self, before: discord.Guild, after: discord.Guild):
        await self.log_event(before, "guild_preferred_locale_update", f"Guild preferred locale updated: {before.preferred_locale} -> {after.preferred_locale}")

    @commands.Cog.listener()
    async def on_guild_onboarding_toggle(self, guild: discord.Guild):
        await self.log_event(guild, "guild_onboarding_toggle", f"Guild onboarding toggled: {guild.name}")

    @commands.Cog.listener()
    async def on_guild_onboarding_channels_update(self, guild: discord.Guild, before, after):
        await self.log_event(guild, "guild_onboarding_channels_update", f"Guild onboarding channels updated: {guild.name}")

    @commands.Cog.listener()
    async def on_guild_onboarding_question_add(self, guild: discord.Guild, question):
        await self.log_event(guild, "guild_onboarding_question_add", f"Guild onboarding question added: {guild.name}")

    @commands.Cog.listener()
    async def on_guild_onboarding_question_remove(self, guild: discord.Guild, question):
        await self.log_event(guild, "guild_onboarding_question_remove", f"Guild onboarding question removed: {guild.name}")

    @commands.Cog.listener()
    async def on_guild_onboarding_update(self, guild: discord.Guild, before, after):
        await self.log_event(guild, "guild_onboarding_update", f"Guild onboarding updated: {guild.name}")

    @commands.Cog.listener()
    async def on_ban_add(self, guild: discord.Guild, user: discord.User):
        await self.log_event(guild, "ban_add", f"User banned: {user.name}")

    @commands.Cog.listener()
    async def on_ban_remove(self, guild: discord.Guild, user: discord.User):
        await self.log_event(guild, "ban_remove", f"User unbanned: {user.name}")

    @commands.Cog.listener()
    async def on_case_delete(self, case):
        await self.log_event(case.guild, "case_delete", f"Case deleted: {case.id}")

    @commands.Cog.listener()
    async def on_case_update(self, before, after):
        await self.log_event(before.guild, "case_update", f"Case updated: {before.id} -> {after.id}")

    @commands.Cog.listener()
    async def on_kick_add(self, guild: discord.Guild, user: discord.User):
        await self.log_event(guild, "kick_add", f"User kicked: {user.name}")

    @commands.Cog.listener()
    async def on_kick_remove(self, guild: discord.Guild, user: discord.User):
        await self.log_event(guild, "kick_remove", f"User kick removed: {user.name}")

    @commands.Cog.listener()
    async def on_mute_add(self, guild: discord.Guild, user: discord.User):
        await self.log_event(guild, "mute_add", f"User muted: {user.name}")

    @commands.Cog.listener()
    async def on_mute_remove(self, guild: discord.Guild, user: discord.User):
        await self.log_event(guild, "mute_remove", f"User unmuted: {user.name}")

    @commands.Cog.listener()
    async def on_warn_add(self, guild: discord.Guild, user: discord.User):
        await self.log_event (guild, "warn_add", f"User warned: {user.name}")

    @commands.Cog.listener()
    async def on_warn_remove(self, guild: discord.Guild, user: discord.User):
        await self.log_event(guild, "warn_remove", f"User warn removed: {user.name}")

    @commands.Cog.listener()
    async def on_report_create(self, report):
        await self.log_event(report.guild, "report_create", f"Report created: {report.id}")

    @commands.Cog.listener()
    async def on_reports_ignore(self, report):
        await self.log_event(report.guild, "reports_ignore", f"Report ignored: {report.id}")

    @commands.Cog.listener()
    async def on_reports_accept(self, report):
        await self.log_event(report.guild, "reports_accept", f"Report accepted: {report.id}")

    @commands.Cog.listener()
    async def on_user_note_add(self, user: discord.User, note):
        await self.log_event(user.guild, "user_note_add", f"Note added to user {user.name}: {note}")

    @commands.Cog.listener()
    async def on_user_note_remove(self, user: discord.User, note):
        await self.log_event(user.guild, "user_note_remove", f"Note removed from user {user.name}: {note}")
