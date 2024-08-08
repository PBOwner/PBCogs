from redbot.core import commands, Config  # isort:skip
from redbot.core.bot import Red  # isort:skip
from redbot.core.i18n import Translator, cog_i18n  # isort:skip
import discord  # isort:skip
import typing  # isort:skip

from AAA3A_utils.settings import Settings  # Import the Settings class
from .dashboard_integration import DashboardIntegration

# Credits:
# General repo credits.

_: Translator = Translator("EventLogger", __file__)

@cog_i18n(_)
class EventLogger(DashboardIntegration, commands.Cog):
  """Cog to log various Discord events"""

  def __init__(self, bot: Red, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.bot = bot
    self.config: Config = Config.get_conf(
      self,
      identifier=1234567890,
      force_registration=True,
    )
    self.config.register_guild(
      channels={},
      command_log_channel=None,
    )

    _settings: typing.Dict[
      str, typing.Dict[str, typing.Union[typing.List[str], bool, str]]
    ] = {
      "channels": {
        "converter": dict,
        "description": "Mapping of events to channel IDs for logging.",
      },
      "command_log_channel": {
        "converter": int,
        "description": "Channel ID for logging commands.",
      },
    }
    self.settings: Settings = Settings(
      bot=self.bot,
      cog=self,
      config=self.config,
      group=self.config.GUILD,
      settings=_settings,
      global_path=[],
      use_profiles_system=False,
      can_edit=True,
      commands_group=self.config,
    )

    self.event_queue = asyncio.Queue()
    self.bot.loop.create_task(self.process_event_queue())

  async def cog_load(self) -> None:
    await super().cog_load()
    await self.settings.add_commands()
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
            "app": ["integration_create", "integration_delete", "integration_update"],
            "automod": ["automod_rule_create", "automod_rule_delete", "automod_rule_update"],
            "ban": ["member_ban", "member_unban"],
            "channel": ["guild_channel_bitrate_update", "guild_channel_create", "guild_channel_delete", "guild_channel_name_update", "guild_channel_nsfw_update", "guild_channel_parent_update", "guild_channel_permissions_update", "guild_channel_pins_update", "guild_channel_rtc_region_update", "guild_channel_slowmode_update", "guild_channel_topic_update", "guild_channel_type_update", "guild_channel_user_limit_update", "guild_channel_video_quality_update", "guild_channel_default_archive_duration_update", "guild_channel_default_thread_slowmode_update", "guild_channel_default_reaction_emoji_update", "guild_channel_default_sort_order_update", "guild_channel_forum_tags_update", "guild_channel_forum_layout_update"],
            "commands": ["command_executed"],
            "emoji": ["guild_emoji_create", "guild_emoji_delete", "guild_emoji_update", "guild_emojis_update"],
            "event": ["scheduled_event_create", "scheduled_event_delete", "scheduled_event_update", "scheduled_event_user_add", "scheduled_event_user_remove"],
            "invite": ["invite_create", "invite_delete"],
            "message": ["bulk_message_delete", "message_delete", "message_edit"],
            "moderation": ["ban_add", "ban_remove", "case_delete", "case_update", "kick_add", "kick_remove", "mute_add", "mute_remove", "report_create", "reports_accept", "reports_ignore", "user_note_add", "user_note_remove", "warn_add", "warn_remove"],
            "onboarding": ["guild_onboarding_channels_update", "guild_onboarding_question_add", "guild_onboarding_question_remove", "guild_onboarding_toggle", "guild_onboarding_update"],
            "reaction": ["reaction_add", "reaction_remove"],
            "role": ["guild_role_create", "guild_role_delete", "guild_role_update"],
            "server": ["guild_afk_channel_update", "guild_afk_timeout_update", "guild_banner_update", "guild_boost_level_update", "guild_boost_progress_bar_update", "guild_description_update", "guild_discovery_splash_update", "guild_explicit_content_filter_update", "guild_features_update", "guild_icon_update", "guild_message_notifications_update", "guild_mfa_level_update", "guild_name_update", "guild_partner_status_update", "guild_preferred_locale_update", "guild_public_updates_channel_update", "guild_rules_channel_update", "guild_splash_update", "guild_system_channel_update", "guild_update", "guild_vanity_url_update", "guild_verification_level_update", "guild_verified_update", "guild_widget_update"],
            "soundboard": ["soundboard_sound_delete", "soundboard_sound_emoji_update", "soundboard_sound_name_update", "soundboard_sound_upload", "soundboard_sound_volume_update"],
            "sticker": ["guild_sticker_create", "guild_sticker_delete", "guild_sticker_update"],
            "thread": ["thread_create", "thread_delete", "thread_member_join", "thread_member_remove", "thread_update"],
            "typing": ["typing"],
            "user": ["member_update", "user_avatar_update", "user_roles_add", "user_roles_remove", "user_roles_update", "user_timeout", "user_timeout_remove", "user_update"],
            "voice": ["voice_state_update"],
            "webhook": ["webhook_create", "webhook_delete", "webhook_update"]
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
        command_log_channel_id = await self.config.guild(ctx.guild).command_log_channel()
        if not channels and not command_log_channel_id:
            await ctx.send("No logging channels set.")
            return
        message = "Current logging channels:\n"
        for event, channel_id in sorted(channels.items()):
            channel = ctx.guild.get_channel(channel_id)
            if channel:
                message += f"{event}: {channel.mention}\n"
        if command_log_channel_id:
            command_log_channel = ctx.guild.get_channel(command_log_channel_id)
            if command_log_channel:
                message += f"Command Log: {command_log_channel.mention}\n"
        await ctx.send(message)

    @setlog.command()
    async def categories(self, ctx):
        """View the event categories and their events"""
        event_categories = {
            "app": ["integration_create", "integration_delete", "integration_update"],
            "automod": ["automod_rule_create", "automod_rule_delete", "automod_rule_update"],
            "ban": ["member_ban", "member_unban"],
            "channel": ["guild_channel_bitrate_update", "guild_channel_create", "guild_channel_delete", "guild_channel_name_update", "guild_channel_nsfw_update", "guild_channel_parent_update", "guild_channel_permissions_update", "guild_channel_pins_update", "guild_channel_rtc_region_update", "guild_channel_slowmode_update", "guild_channel_topic_update", "guild_channel_type_update", "guild_channel_user_limit_update", "guild_channel_video_quality_update", "guild_channel_default_archive_duration_update", "guild_channel_default_thread_slowmode_update", "guild_channel_default_reaction_emoji_update", "guild_channel_default_sort_order_update", "guild_channel_forum_tags_update", "guild_channel_forum_layout_update"],
            "commands": ["command_executed"],
            "emoji": ["guild_emoji_create", "guild_emoji_delete", "guild_emoji_update", "guild_emojis_update"],
            "event": ["scheduled_event_create", "scheduled_event_delete", "scheduled_event_update", "scheduled_event_user_add", "scheduled_event_user_remove"],
            "invite": ["invite_create", "invite_delete"],
            "message": ["bulk_message_delete", "message_delete", "message_edit"],
            "moderation": ["ban_add", "ban_remove", "case_delete", "case_update", "kick_add", "kick_remove", "mute_add", "mute_remove", "report_create", "reports_accept", "reports_ignore", "user_note_add", "user_note_remove", "warn_add", "warn_remove"],
            "onboarding": ["guild_onboarding_channels_update", "guild_onboarding_question_add", "guild_onboarding_question_remove", "guild_onboarding_toggle", "guild_onboarding_update"],
            "reaction": ["reaction_add", "reaction_remove"],
            "role": ["guild_role_create", "guild_role_delete", "guild_role_update"],
            "server": ["guild_afk_channel_update", "guild_afk_timeout_update", "guild_banner_update", "guild_boost_level_update", "guild_boost_progress_bar_update", "guild_description_update", "guild_discovery_splash_update", "guild_explicit_content_filter_update", "guild_features_update", "guild_icon_update", "guild_message_notifications_update", "guild_mfa_level_update", "guild_name_update", "guild_partner_status_update", "guild_preferred_locale_update", "guild_public_updates_channel_update", "guild_rules_channel_update", "guild_splash_update", "guild_system_channel_update", "guild_vanity_url_update", "guild_verification_level_update", "guild_verified_update", "guild_widget_update"],
            "soundboard": ["soundboard_sound_delete", "soundboard_sound_emoji_update", "soundboard_sound_name_update", "soundboard_sound_upload", "soundboard_sound_volume_update"],
            "sticker": ["guild_sticker_create", "guild_sticker_delete", "guild_sticker_update"],
            "thread": ["thread_create", "thread_delete", "thread_member_join", "thread_member_remove", "thread_update"],
            "typing": ["typing"],
            "user": ["member_update", "user_avatar_update", "user_roles_add", "user_roles_remove", "user_roles_update", "user_timeout", "user_timeout_remove", "user_update"],
            "voice": ["voice_state_update"],
            "webhook": ["webhook_create", "webhook_delete", "webhook_update"]
        }
        embed = discord.Embed(title="Event Categories and Their Events", color=discord.Color.blue())
        for category, events in sorted(event_categories.items()):
            embed.add_field(name=category.capitalize(), value="\n".join(sorted(events)), inline=False)
        await ctx.send(embed=embed)

    # Event listeners
    @commands.Cog.listener()
    async def on_integration_create(self, integration: discord.Integration):
        description = (
            f"**Integration:** {integration.name}\n"
            f"**Integration ID:** `{integration.id}`\n"
            f"**Guild:** ||{integration.guild.name} ({integration.guild.id})||\n"
            f"**Timestamp:** <t:{int(integration.created_at.timestamp())}:F>"
        )
        await self.log_event(integration.guild, "integration_create", description)

    @commands.Cog.listener()
    async def on_integration_delete(self, integration: discord.Integration):
        description = (
            f"**Integration:** {integration.name}\n"
            f"**Integration ID:** `{integration.id}`\n"
            f"**Guild:** ||{integration.guild.name} ({integration.guild.id})||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(integration.guild, "integration_delete", description)

    @commands.Cog.listener()
    async def on_integration_update(self, integration: discord.Integration):
        description = (
            f"**Integration:** {integration.name}\n"
            f"**Integration ID:** `{integration.id}`\n"
            f"**Guild:** ||{integration.guild.name} ({integration.guild.id})||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(integration.guild, "integration_update", description)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        description = (
            f"**Channel:** {channel.name}\n"
            f"**Channel ID:** `{channel.id}`\n"
            f"**Channel Type:** {str(channel.type)}\n"
            f"**Guild:** ||{channel.guild.name} ({channel.guild.id})||\n"
            f"**Creator:** {channel.guild.me.name if channel.guild.me else 'N/A'}\n"
            f"**Creator ID:** ||{channel.guild.me.id if channel.guild.me else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(channel.guild, "guild_channel_create", description)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        description = (
            f"**Channel:** {channel.name}\n"
            f"**Channel ID:** `{channel.id}`\n"
            f"**Channel Type:** {str(channel.type)}\n"
            f"**Guild:** ||{channel.guild.name} ({channel.guild.id})||\n"
            f"**Deleter:** {channel.guild.me.name if channel.guild.me else 'N/A'}\n"
            f"**Deleter ID:** ||{channel.guild.me.id if channel.guild.me else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(channel.guild, "guild_channel_delete", description)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        if before.position != after.position:  # Ignore position updates
            return
        description = (
            f"**Before Channel:** {before.name}\n"
            f"**After Channel:** {after.name}\n"
            f"**Channel ID:** `{before.id}`\n"
            f"**Guild:** ||{before.guild.name} ({before.guild.id})||\n"
            f"**Updater:** {before.guild.me.name if before.guild.me else 'N/A'}\n"
            f"**Updater ID:** ||{before.guild.me.id if before.guild.me else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(before.guild, "guild_channel_update", description)

    @commands.Cog.listener()
    async def on_guild_channel_pins_update(self, channel: discord.abc.GuildChannel, last_pin: discord.Message):
        description = (
            f"**Channel:** {channel.name}\n"
            f"**Channel ID:** `{channel.id}`\n"
            f"**Guild:** ||{channel.guild.name} ({channel.guild.id})||\n"
            f"**Last Pin:** {last_pin.content if last_pin else 'None'}\n"
            f"**Pinner:** {last_pin.author.name if last_pin else 'N/A'}\n"
            f"**Pinner ID:** ||{last_pin.author.id if last_pin else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(channel.guild, "guild_channel_pins_update", description)

    @commands.Cog.listener()
    async def on_guild_channel_name_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        description = (
            f"**Before Name:** {before.name}\n"
            f"**After Name:** {after.name}\n"
            f"**Channel ID:** `{before.id}`\n"
            f"**Guild:** ||{before.guild.name} ({before.guild.id})||\n"
            f"**Updater:** {before.guild.me.name if before.guild.me else 'N/A'}\n"
            f"**Updater ID:** ||{before.guild.me.id if before.guild.me else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(before.guild, "guild_channel_name_update", description)

    @commands.Cog.listener()
    async def on_guild_channel_topic_update(self, before: discord.TextChannel, after: discord.TextChannel):
        description = (
            f"**Before Topic:** {before.topic}\n"
            f"**After Topic:** {after.topic}\n"
            f"**Channel ID:** `{before.id}`\n"
            f"**Guild:** ||{before.guild.name} ({before.guild.id})||\n"
            f"**Updater:** {before.guild.me.name if before.guild.me else 'N/A'}\n"
            f"**Updater ID:** ||{before.guild.me.id if before.guild.me else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(before.guild, "guild_channel_topic_update", description)

    @commands.Cog.listener()
    async def on_guild_channel_nsfw_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        description = (
            f"**Before NSFW:** {before.is_nsfw()}\n"
            f"**After NSFW:** {after.is_nsfw()}\n"
            f"**Channel ID:** `{before.id}`\n"
            f"**Guild:** ||{before.guild.name} ({before.guild.id} else `N/A`||\n"
            f"**Updater:** {before.guild.me.name if before.guild.me else 'N/A'}\n"
            f"**Updater ID:** ||{before.guild.me.id if before.guild.me else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(before.guild, "guild_channel_nsfw_update", description)

    @commands.Cog.listener()
    async def on_guild_channel_parent_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        description = (
            f"**Before Parent:** {before.category.name if before.category else 'None'}\n"
            f"**After Parent:** {after.category.name if after.category else 'None'}\n"
            f"**Channel ID:** `{before.id}`\n"
            f"**Guild:** ||{before.guild.name} ({before.guild.id})||\n"
            f"**Updater:** {before.guild.me.name if before.guild.me else 'N/A'}\n"
            f"**Updater ID:** ||{before.guild.me.id if before.guild.me else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(before.guild, "guild_channel_parent_update", description)

    @commands.Cog.listener()
    async def on_guild_channel_permissions_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        description = (
            f"**Before Permissions:** {str(before.overwrites)}\n"
            f"**After Permissions:** {str(after.overwrites)}\n"
            f"**Channel ID:** `{before.id}`\n"
            f"**Guild:** ||{before.guild.name} ({before.guild.id})||\n"
            f"**Updater:** {before.guild.me.name if before.guild.me else 'N/A'}\n"
            f"**Updater ID:** ||{before.guild.me.id if before.guild.me else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(before.guild, "guild_channel_permissions_update", description)

    @commands.Cog.listener()
    async def on_guild_channel_type_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        description = (
            f"**Before Type:** {str(before.type)}\n"
            f"**After Type:** {str(after.type)}\n"
            f"**Channel ID:** `{before.id}`\n"
            f"**Guild:** ||{before.guild.name} ({before.guild.id})||\n"
            f"**Updater:** {before.guild.me.name if before.guild.me else 'N/A'}\n"
            f"**Updater ID:** ||{before.guild.me.id if before.guild.me else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(before.guild, "guild_channel_type_update", description)

    @commands.Cog.listener()
    async def on_guild_channel_bitrate_update(self, before: discord.VoiceChannel, after: discord.VoiceChannel):
        description = (
            f"**Before Bitrate:** {before.bitrate}\n"
            f"**After Bitrate:** {after.bitrate}\n"
            f"**Channel ID:** `{before.id}`\n"
            f"**Guild:** ||{before.guild.name} ({before.guild.id})||\n"
            f"**Updater:** {before.guild.me.name if before.guild.me else 'N/A'}\n"
            f"**Updater ID:** ||{before.guild.me.id if before.guild.me else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(before.guild, "guild_channel_bitrate_update", description)

    @commands.Cog.listener()
    async def on_guild_channel_user_limit_update(self, before: discord.VoiceChannel, after: discord.VoiceChannel):
        description = (
            f"**Before User Limit:** {before.user_limit}\n"
            f"**After User Limit:** {after.user_limit}\n"
            f"**Channel ID:** `{before.id}`\n"
            f"**Guild:** ||{before.guild.name} ({before.guild.id})||\n"
            f"**Updater:** {before.guild.me.name if before.guild.me else 'N/A'}\n"
            f"**Updater ID:** ||{before.guild.me.id if before.guild.me else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(before.guild, "guild_channel_user_limit_update", description)

    @commands.Cog.listener()
    async def on_guild_channel_slowmode_update(self, before: discord.TextChannel, after: discord.TextChannel):
        description = (
            f"**Before Slowmode:** {before.slowmode_delay}\n"
            f"**After Slowmode:** {after.slowmode_delay}\n"
            f"**Channel ID:** `{before.id}`\n"
            f"**Guild:** ||{before.guild.name} ({before.guild.id})||\n"
            f"**Updater:** {before.guild.me.name if before.guild.me else 'N/A'}\n"
            f"**Updater ID:** ||{before.guild.me.id if before.guild.me else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(before.guild, "guild_channel_slowmode_update", description)

    @commands.Cog.listener()
    async def on_guild_channel_rtc_region_update(self, before: discord.VoiceChannel, after: discord.VoiceChannel):
        description = (
            f"**Before RTC Region:** {before.rtc_region}\n"
            f"**After RTC Region:** {after.rtc_region}\n"
            f"**Channel ID:** `{before.id}`\n"
            f"**Guild:** ||{before.guild.name} ({before.guild.id})||\n"
            f"**Updater:** {before.guild.me.name if before.guild.me else 'N/A'}\n"
            f"**Updater ID:** ||{before.guild.me.id if before.guild.me else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(before.guild, "guild_channel_rtc_region_update", description)

    @commands.Cog.listener()
    async def on_guild_channel_video_quality_update(self, before: discord.VoiceChannel, after: discord.VoiceChannel):
        description = (
            f"**Before Video Quality:** {before.video_quality_mode}\n"
            f"**After Video Quality:** {after.video_quality_mode}\n"
            f"**Channel ID:** `{before.id}`\n"
            f"**Guild:** ||{before.guild.name} ({before.guild.id})||\n"
            f"**Updater:** {before.guild.me.name if before.guild.me else 'N/A'}\n"
            f"**Updater ID:** ||{before.guild.me.id if before.guild.me else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(before.guild, "guild_channel_video_quality_update", description)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        description = (
            f"**Member:** {member.name} ({member.mention})\n"
            f"**Member ID:** `{member.id}`\n"
            f"**Guild:** ||{member.guild.name} ({member.guild.id})||\n"
            f"**Before Channel:** {str(before.channel) if before.channel else 'None'}\n"
            f"**After Channel:** {str(after.channel) if after.channel else 'None'}\n"
            f"**Before Mute:** {before.mute}\n"
            f"**After Mute:** {after.mute}\n"
            f"**Before Deaf:** {before.deaf}\n"
            f"**After Deaf:** {after.deaf}\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(member.guild, "voice_state_update", description)

    @commands.Cog.listener()
    async def on_automod_rule_create(self, rule: discord.AutoModRule):
        description = (
            f"**Rule:** {rule.name}\n"
            f"**Rule ID:** `{rule.id}`\n"
            f"**Guild:** ||{rule.guild.name} ({rule.guild.id})||\n"
            f"**Creator:** {rule.creator.name if rule.creator else 'N/A'}\n"
            f"**Creator ID:** ||{rule.creator.id if rule.creator else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(rule.created_at.timestamp())}:F>"
        )
        await self.log_event(rule.guild, "automod_rule_create", description)

    @commands.Cog.listener()
    async def on_automod_rule_delete(self, rule: discord.AutoModRule):
        description = (
            f"**Rule:** {rule.name}\n"
            f"**Rule ID:** `{rule.id}`\n"
            f"**Guild:** ||{rule.guild.name} ({rule.guild.id})||\n"
            f"**Deleter:** {rule.creator.name if rule.creator else 'N/A'}\n"
            f"**Deleter ID:** ||{rule.creator.id if rule.creator else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(rule.guild, "automod_rule_delete", description)

    @commands.Cog.listener()
    async def on_automod_rule_update(self, before: discord.AutoModRule, after: discord.AutoModRule):
        description = (
            f"**Before Rule:** {before.name}\n"
            f"**After Rule:** {after.name}\n"
            f"**Rule ID:** `{before.id}`\n"
            f"**Guild:** ||{before.guild.name} ({before.guild.id})||\n"
            f"**Updater:** {before.creator.name if before.creator else 'N/A'}\n"
            f"**Updater ID:** ||{before.creator.id if before.creator else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(before.guild, "automod_rule_update", description)

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild: discord.Guild, before: list[discord.Emoji], after: list[discord.Emoji]):
        description = (
            f"**Guild:** ||{guild.name} ({guild.id})||\n"
            f"**Before Emojis:** {', '.join([emoji.name for emoji in before])}\n"
            f"**After Emojis:** {', '.join([emoji.name for emoji in after])}\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(guild, "guild_emojis_update", description)

    @commands.Cog.listener()
    async def on_guild_emoji_create(self, emoji: discord.Emoji):
        description = (
            f"**Emoji:** {emoji} ({emoji.name})\n"
            f"**Emoji ID:** `{emoji.id}`\n"
            f"**Guild:** ||{emoji.guild.name} ({emoji.guild.id})||\n"
            f"**Creator:** {emoji.user.name if emoji.user else 'N/A'}\n"
            f"**Creator ID:** ||{emoji.user.id if emoji.user else 'N/A'}||\n"
            f"**Created At:** <t:{int(emoji.created_at.timestamp())}:F>"
        )
        embed = discord.Embed(
            title="Emoji Created",
            description=description,
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=emoji.url)
        await self.log_event(emoji.guild, "guild_emoji_create", description)

    @commands.Cog.listener()
    async def on_guild_emoji_delete(self, emoji: discord.Emoji):
        description = (
            f"**Emoji:** {emoji} ({emoji.name})\n"
            f"**Emoji ID:** `{emoji.id}`\n"
            f"**Guild:** ||{emoji.guild.name} ({emoji.guild.id})||\n"
            f"**Deleter:** {emoji.user.name if emoji.user else 'N/A'}\n"
            f"**Deleter ID:** ||{emoji.user.id if emoji.user else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        embed = discord.Embed(
            title="Emoji Deleted",
            description=description,
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=emoji.url)
        await self.log_event(emoji.guild, "guild_emoji_delete", description)

    @commands.Cog.listener()
    async def on_guild_emoji_update(self, before: discord.Emoji, after: discord.Emoji):
        description = (
            f"**Before Emoji:** {before} ({before.name})\n"
            f"**After Emoji:** {after} ({after.name})\n"
            f"**Emoji ID:** `{before.id}`\n"
            f"**Guild:** ||{before.guild.name} ({before.guild.id})||\n"
            f"**Updater:** {before.user.name if before.user else 'N/A'}\n"
            f"**Updater ID:** ||{before.user.id if before.user else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        embed = discord.Embed(
            title="Emoji Updated",
            description=description,
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=after.url)
        await self.log_event(before.guild, "guild_emoji_update", description)

    @commands.Cog.listener()
    async def on_scheduled_event_create(self, event: discord.ScheduledEvent):
        description = (
            f"**Event:** {event.name}\n"
            f"**Event ID:** `{event.id}`\n"
            f"**Guild:** ||{event.guild.name} ({event.guild.id})||\n"
            f"**Creator:** {event.creator.name if event.creator else 'N/A'}\n"
            f"**Creator ID:** ||{event.creator.id if event.creator else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(event.created_at.timestamp())}:F>"
        )
        await self.log_event(event.guild, "scheduled_event_create", description)

    @commands.Cog.listener()
    async def on_scheduled_event_delete(self, event: discord.ScheduledEvent):
        description = (
            f"**Event:** {event.name}\n"
            f"**Event ID:** `{event.id}`\n"
            f"**Guild:** ||{event.guild.name} ({event.guild.id})||\n"
            f"**Deleter:** {event.creator.name if event.creator else 'N/A'}\n"
            f"**Deleter ID:** ||{event.creator.id if event.creator else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(event.guild, "scheduled_event_delete", description)

    @commands.Cog.listener()
    async def on_scheduled_event_update(self, before: discord.ScheduledEvent, after: discord.ScheduledEvent):
        description = (
            f"**Before Event:** {before.name}\n"
            f"**After Event:** {after.name}\n"
            f"**Event ID:** `{before.id}`\n"
            f"**Guild:** ||{before.guild.name} ({before.guild.id})||\n"
            f"**Updater:** {before.creator.name if before.creator else 'N/A'}\n"
            f"**Updater ID:** ||{before.creator.id if before.creator else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(before.guild, "scheduled_event_update", description)

    @commands.Cog.listener()
    async def on_scheduled_event_user_add(self, event: discord.ScheduledEvent, user: discord.User):
        description = (
            f"**User:** {user.name}\n"
            f"**User ID:** `{user.id}`\n"
            f"**Event:** {event.name}\n"
            f"**Event ID:** `{event.id}`\n"
            f"**Guild:** ||{event.guild.name} ({event.guild.id})||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(event.guild, "scheduled_event_user_add", description)

    @commands.Cog.listener()
    async def on_scheduled_event_user_remove(self, event: discord.ScheduledEvent, user: discord.User):
        description = (
            f"**User:** {user.name}\n"
            f"**User ID:** `{user.id}`\n"
            f"**Event:** {event.name}\n"
            f"**Event ID:** `{event.id}`\n"
            f"**Guild:** ||{event.guild.name} ({event.guild.id})||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(event.guild, "scheduled_event_user_remove", description)

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        description = (
            f"**Invite URL:** {invite.url}\n"
            f"**Invite ID:** `{invite.id}`\n"
            f"**Guild:** ||{invite.guild.name} ({invite.guild.id})||\n"
            f"**Channel:** {invite.channel.name}\n"
            f"**Channel ID:** `{invite.channel.id}`\n"
            f"**Creator:** {invite.inviter.name if invite.inviter else 'N/A'}\n"
            f"**Creator ID:** ||{invite.inviter.id if invite.inviter else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(invite.created_at.timestamp())}:F>"
        )
        await self.log_event(invite.guild, "invite_create", description)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        description = (
            f"**Invite URL:** {invite.url}\n"
            f"**Invite ID:** `{invite.id}`\n"
            f"**Guild:** ||{invite.guild.name} ({invite.guild.id})||\n"
            f"**Channel:** {invite.channel.name}\n"
            f"**Channel ID:** `{invite.channel.id}`\n"
            f"**Deleter:** {invite.inviter.name if invite.inviter else 'N/A'}\n"
            f"**Deleter ID:** ||{invite.inviter.id if invite.inviter else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(invite.guild, "invite_delete", description)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.guild is None:  # Ignore DMs
            return
        description = (
            f"**Message Content:** {message.content}\n"
            f"**Message ID:** `{message.id}`\n"
            f"**Author:** {message.author.name} ({message.author.mention})\n"
            f"**Author ID:** `{message.author.id}`\n"
            f"**Channel:** {message.channel.name}\n"
            f"**Channel ID:** `{message.channel.id}`\n"
            f"**Guild:** ||{message.guild.name} ({message.guild.id})||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(message.guild, "message_delete", description)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages: list[discord.Message]):
        if messages[0].guild is None:  # Ignore DMs
            return
        description = (
            f"**Message Count:** {len(messages)}\n"
            f"**Channel:** {messages[0].channel.name}\n"
            f"**Channel ID:** `{messages[0].channel.id}`\n"
            f"**Guild:** ||{messages[0].guild.name} ({messages[0].guild.id})||\n"
            f"**Messages:** {', '.join([message.content for message in messages])}\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(messages[0].guild, "bulk_message_delete", description)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.guild is None:  # Ignore DMs
            return
        description = (
            f"**Before Content:** {before.content}\n"
            f"**After Content:** {after.content}\n"
            f"**Message ID:** `{before.id}`\n"
            f"**Author:** {before.author.name} ({before.author.mention})\n"
            f"**Author ID:** `{before.author.id}`\n"
            f"**Channel:** {before.channel.name}\n"
            f"**Channel ID:** `{before.channel.id}`\n"
            f"**Guild:** ||{before.guild.name} ({before.guild.id})||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(before.guild, "message_edit", description)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        description = (
            f"**Role:** {role.name}\n"
            f"**Role ID:** `{role.id}`\n"
            f"**Guild:** ||{role.guild.name} ({role.guild.id})||\n"
            f"**Creator:** {role.guild.me.name if role.guild.me else 'N/A'}\n"
            f"**Creator ID:** ||{role.guild.me.id if role.guild.me else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(role.guild, "guild_role_create", description)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        description = (
            f"**Role:** {role.name}\n"
            f"**Role ID:** `{role.id}`\n"
            f"**Guild:** ||{role.guild.name} ({role.guild.id})||\n"
            f"**Deleter:** {role.guild.me.name if role.guild.me else 'N/A'}\n"
            f"**Deleter ID:** ||{role.guild.me.id if role.guild.me else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(role.guild, "guild_role_delete", description)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        description = (
            f"**Before Role:** {before.name}\n"
            f"**After Role:** {after.name}\n"
            f"**Role ID:** `{before.id}`\n"
            f"**Guild:** ||{before.guild.name} ({before.guild.id})||\n"
            f"**Updater:** {before.guild.me.name if before.guild.me else 'N/A'}\n"
            f"**Updater ID:** ||{before.guild.me.id if before.guild.me else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(before.guild, "guild_role_update", description)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        description = (
            f"**User:** {user.name} ({user.mention})\n"
            f"**User ID:** `{user.id}`\n"
            f"**Guild:** ||{guild.name} ({guild.id})||\n"
            f"**Banner:** {guild.me.name if guild.me else 'N/A'}\n"
            f"**Banner ID:** ||{guild.me.id if guild.me else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(guild, "member_ban", description)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        description = (
            f"**User:** {user.name} ({user.mention})\n"
            f"**User ID:** `{user.id}`\n"
            f"**Guild:** ||{guild.name} ({guild.id})||\n"
            f"**Unbanner:** {guild.me.name if guild.me else 'N/A'}\n"
            f"**Unbanner ID:** ||{guild.me.id if guild.me else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(guild, "member_unban", description)

    @commands.Cog.listener()
    async def on_user_update(self, before: discord.User, after: discord.User):
        description = (
            f"**Before Name:** {before.name}\n"
            f"**After Name:** {after.name}\n"
            f"**User ID:** `{before.id}`\n"
            f"**Before Discriminator:** {before.discriminator}\n"
            f"**After Discriminator:** {after.discriminator}\n"
            f"**Before Avatar:** {str(before.avatar.url)}\n"
            f"**After Avatar:** {str(after.avatar.url)}\n"
            f"**Before Bot:** {before.bot}\n"
            f"**After Bot:** {after.bot}\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(None, "user_update", description)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        description = (
            f"**Before Name:** {before.name}\n"
            f"**After Name:** {after.name}\n"
            f"**Member ID:** `{before.id}`\n"
            f"**Guild:** ||{before.guild.name} ({before.guild.id})||\n"
            f"**Before Nick:** {before.nick}\n"
            f"**After Nick:** {after.nick}\n"
            f"**Before Roles:** {', '.join([role.name for role in before.roles])}\n"
            f"**After Roles:** {', '.join([role.name for role in after.roles])}\n"
            f"**Before Status:** {str(before.status)}\n"
            f"**After Status:** {str(after.status)}\n"
            f"**Before Activity:** {str(before.activity)}\n"
            f"**After Activity:** {str(after.activity)}\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(before.guild, "member_update", description)

    @commands.Cog.listener()
    async def on_user_roles_update(self, before: discord.Member, after: discord.Member):
        description = (
            f"**Member:** {before.name}\n"
            f"**Member ID:** `{before.id}`\n"
            f"**Before Roles:** {', '.join([role.name for role in before.roles])}\n"
            f"**After Roles:** {', '.join([role.name for role in after.roles])}\n"
            f"**Guild:** ||{before.guild.name} ({before.guild.id})||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(before.guild, "user_roles_update", description)

    @commands.Cog.listener()
    async def on_user_roles_add(self, member: discord.Member, role: discord.Role):
        description = (
            f"**Member:** {member.name}\n"
            f"**Member ID:** `{member.id}`\n"
            f"**Role Added:** {role.name}\n"
            f"**Role ID:** `{role.id}`\n"
            f"**Guild:** ||{member.guild.name} ({member.guild.id})||\n"
            f"**Adder:** {member.guild.me.name if member.guild.me else 'N/A'}\n"
            f"**Adder ID:** ||{member.guild.me.id if member.guild.me else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(member.guild, "user_roles_add", description)

    @commands.Cog.listener()
    async def on_user_roles_remove(self, member: discord.Member, role: discord.Role):
        description = (
            f"**Member:** {member.name}\n"
            f"**Member ID:** `{member.id}`\n"
            f"**Role Removed:** {role.name}\n"
            f"**Role ID:** `{role.id}`\n"
            f"**Guild:** ||{member.guild.name} ({member.guild.id})||\n"
            f"**Remover:** {member.guild.me.name if member.guild.me else 'N/A'}\n"
            f"**Remover ID:** ||{member.guild.me.id if member.guild.me else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(member.guild, "user_roles_remove", description)

    @commands.Cog.listener()
    async def on_user_avatar_update(self, before: discord.User, after: discord.User):
        description = (
            f"**User:** {before.name}\n"
            f"**User ID:** `{before.id}`\n"
            f"**Before Avatar:** {str(before.avatar.url)}\n"
            f"**After Avatar:** {str(after.avatar.url)}\n"
            f"**Guild:** ||{before.guild.name if before.guild else 'DM'} ({before.guild.id if before.guild else 'DM'})||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(before.guild, "user_avatar_update", description)

    @commands.Cog.listener()
    async def on_user_timeout(self, member: discord.Member):
        description = (
            f"**Member:** {member.name}\n"
            f"**Member ID:** `{member.id}`\n"
            f"**Guild:** ||{member.guild.name} ({member.guild.id})||\n"
            f"**Timeout By:** {member.guild.me.name if member.guild.me else 'N/A'}\n"
            f"**Timeout By ID:** ||{member.guild.me.id if member.guild.me else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(member.guild, "user_timeout", description)

    @commands.Cog.listener()
    async def on_user_timeout_remove(self, member: discord.Member):
        description = (
            f"**Member:** {member.name}\n"
            f"**Member ID:** `{member.id}`\n"
            f"**Guild:** ||{member.guild.name} ({member.guild.id})||\n"
            f"**Timeout Removed By:** {member.guild.me.name if member.guild.me else 'N/A'}\n"
            f"**Timeout Removed By ID:** ||{member.guild.me.id if member.guild.me else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(member.guild, "user_timeout_remove", description)

    @commands.Cog.listener()
    async def on_webhook_update(self, channel: discord.abc.GuildChannel):
        description = (
            f"**Channel:** {channel.name}\n"
            f"**Channel ID:** `{channel.id}`\n"
            f"**Guild:** ||{channel.guild.name} ({channel.guild.id})||\n"
            f"**Updater:** {channel.guild.me.name if channel.guild.me else 'N/A'}\n"
            f"**Updater ID:** ||{channel.guild.me.id if channel.guild.me else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(channel.guild, "webhook_update", description)

    @commands.Cog.listener()
    async def on_webhook_create(self, webhook: discord.Webhook):
        description = (
            f"**Webhook:** {webhook.name}\n"
            f"**Webhook ID:** `{webhook.id}`\n"
            f"**Channel:** {webhook.channel.name}\n"
            f"**Channel ID:** `{webhook.channel.id}`\n"
            f"**Guild:** ||{webhook.guild.name} ({webhook.guild.id})||\n"
            f"**Creator:** {webhook.user.name if webhook.user else 'N/A'}\n"
            f"**Creator ID:** ||{webhook.user.id if webhook.user else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(webhook.guild, "webhook_create", description)

    @commands.Cog.listener()
    async def on_webhook_delete(self, webhook: discord.Webhook):
        description = (
            f"**Webhook:** {webhook.name}\n"
            f"**Webhook ID:** `{webhook.id}`\n"
            f"**Channel:** {webhook.channel.name}\n"
            f"**Channel ID:** `{webhook.channel.id}`\n"
            f"**Guild:** ||{webhook.guild.name} ({webhook.guild.id})||\n"
            f"**Deleter:** {webhook.user.name if webhook.user else 'N/A'}\n"
            f"**Deleter ID:** ||{webhook.user.id if webhook.user else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(webhook.guild, "webhook_delete", description)

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        description = (
            f"**Thread:** {thread.name}\n"
            f"**Thread ID:** `{thread.id}`\n"
            f"**Guild:** ||{thread.guild.name} ({thread.guild.id})||\n"
            f"**Creator:** {thread.owner.name if thread.owner else 'N/A'}\n"
            f"**Creator ID:** ||{thread.owner.id if thread.owner else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(thread.created_at.timestamp())}:F>"
        )
        await self.log_event(thread.guild, "thread_create", description)

    @commands.Cog.listener()
    async def on_thread_delete(self, thread: discord.Thread):
        description = (
            f"**Thread:** {thread.name}\n"
            f"**Thread ID:** `{thread.id}`\n"
            f"**Guild:** ||{thread.guild.name} ({thread.guild.id})||\n"
            f"**Deleter:** {thread.owner.name if thread.owner else 'N/A'}\n"
            f"**Deleter ID:** ||{thread.owner.id if thread.owner else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(thread.guild, "thread_delete", description)

    @commands.Cog.listener()
    async def on_thread_update(self, before: discord.Thread, after: discord.Thread):
        description = (
            f"**Before Thread:** {before.name}\n"
            f"**After Thread:** {after.name}\n"
            f"**Thread ID:** `{before.id}`\n"
            f"**Guild:** ||{before.guild.name} ({before.guild.id})||\n"
            f"**Updater:** {before.owner.name if before.owner else 'N/A'}\n"
            f"**Updater ID:** ||{before.owner.id if before.owner else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(before.guild, "thread_update", description)

    @commands.Cog.listener()
    async def on_thread_member_join(self, member: discord.ThreadMember):
        description = (
            f"**Member:** {member.name}\n"
            f"**Member ID:** `{member.id}`\n"
            f"**Thread:** {member.thread.name}\n"
            f"**Thread ID:** `{member.thread.id}`\n"
            f"**Guild:** ||{member.guild.name} ({member.guild.id})||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(member.guild, "thread_member_join", description)

    @commands.Cog.listener()
    async def on_thread_member_remove(self, member: discord.ThreadMember):
        description = (
            f"**Member:** {member.name}\n"
            f"**Member ID:** `{member.id}`\n"
            f"**Thread:** {member.thread.name}\n"
            f"**Thread ID:** `{member.thread.id}`\n"
            f"**Guild:** ||{member.guild.name} ({member.guild.id})||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(member.guild, "thread_member_remove", description)

    @commands.Cog.listener()
    async def on_guild_sticker_create(self, sticker: discord.Sticker):
        description = (
            f"**Sticker:** {sticker.name}\n"
            f"**Sticker ID:** `{sticker.id}`\n"
            f"**Guild:** ||{sticker.guild.name} ({sticker.guild.id})||\n"
            f"**Creator:** {sticker.user.name if sticker.user else 'N/A'}\n"
            f"**Creator ID:** ||{sticker.user.id if sticker.user else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(sticker.created_at.timestamp())}:F>"
        )
        await self.log_event(sticker.guild, "guild_sticker_create", description)

    @commands.Cog.listener()
    async def on_guild_sticker_delete(self, sticker: discord.Sticker):
        description = (
            f"**Sticker:** {sticker.name}\n"
            f"**Sticker ID:** `{sticker.id}`\n"
            f"**Guild:** ||{sticker.guild.name} ({sticker.guild.id})||\n"
            f"**Deleter:** {sticker.user.name if sticker.user else 'N/A'}\n"
            f"**Deleter ID:** ||{sticker.user.id if sticker.user else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(sticker.guild, "guild_sticker_delete", description)

    @commands.Cog.listener()
    async def on_guild_sticker_update(self, before: discord.Sticker, after: discord.Sticker):
        description = (
            f"**Before Sticker:** {before.name}\n"
            f"**After Sticker:** {after.name}\n"
            f"**Sticker ID:** `{before.id}`\n"
            f"**Guild:** ||{before.guild.name} ({before.guild.id})||\n"
            f"**Updater:** {before.user.name if before.user else 'N/A'}\n"
            f"**Updater ID:** ||{before.user.id if before.user else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(before.guild, "guild_sticker_update", description)

    @commands.Cog.listener()
    async def on_soundboard_sound_upload(self, sound):
        description = (
            f"**Sound:** {sound.name}\n"
            f"**Sound ID:** `{sound.id}`\n"
            f"**Guild:** ||{sound.guild.name} ({sound.guild.id})||\n"
            f"**Uploader:** {sound.user.name if sound.user else 'N/A'}\n"
            f"**Uploader ID:** ||{sound.user.id if sound.user else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(sound.guild, "soundboard_sound_upload", description)

    @commands.Cog.listener()
    async def on_soundboard_sound_name_update(self, before, after):
        description = (
            f"**Before Sound:** {before.name}\n"
            f"**After Sound:** {after.name}\n"
            f"**Sound ID:** `{before.id}`\n"
            f"**Guild:** ||{before.guild.name} ({before.guild.id})||\n"
            f"**Updater:** {before.user.name if before.user else 'N/A'}\n"
            f"**Updater ID:** ||{before.user.id if before.user else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(before.guild, "soundboard_sound_name_update", description)

    @commands.Cog.listener()
    async def on_soundboard_sound_volume_update(self, before, after):
        description = (
            f"**Before Volume:** {before.volume}\n"
            f"**After Volume:** {after.volume}\n"
            f"**Sound ID:** `{before.id}`\n"
            f"**Guild:** ||{before.guild.name} ({before.guild.id})||\n"
            f"**Updater:** {before.user.name if before.user else 'N/A'}\n"
            f"**Updater ID:** ||{before.user.id if before.user else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(before.guild, "soundboard_sound_volume_update", description)

    @commands.Cog.listener()
    async def on_soundboard_sound_emoji_update(self, before, after):
        description = (
            f"**Before Emoji:** {before.emoji}\n"
            f"**After Emoji:** {after.emoji}\n"
            f"**Sound ID:** `{before.id}`\n"
            f"**Guild:** ||{before.guild.name} ({before.guild.id})||\n"
            f"**Updater:** {before.user.name if before.user else 'N/A'}\n"
            f"**Updater ID:** ||{before.user.id if before.user else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(before.guild, "soundboard_sound_emoji_update", description)

    @commands.Cog.listener()
    async def on_soundboard_sound_delete(self, sound):
        description = (
            f"**Sound:** {sound.name}\n"
            f"**Sound ID:** `{sound.id}`\n"
            f"**Guild:** ||{sound.guild.name} ({sound.guild.id})||\n"
            f"**Deleter:** {sound.user.name if sound.user else 'N/A'}\n"
            f"**Deleter ID:** ||{sound.user.id if sound.user else 'N/A'}||\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(sound.guild, "soundboard_sound_delete", description)

    @commands.Cog.listener()
    async def on_typing(self, channel: discord.abc.Messageable, user: Union[discord.User, discord.Member], when: datetime):
        if isinstance(channel, discord.DMChannel):  # Ignore DMs
            return
        description = (
            f"**User:** {user.name} ({user.mention})\n"
            f"**User ID:** `{user.id}`\n"
            f"**Channel:** {channel.name}\n"
            f"**Channel ID:** `{channel.id}`\n"
            f"**Guild:** ||{channel.guild.name} ({channel.guild.id})||\n"
            f"**Timestamp:** <t:{int(when.timestamp())}:F>"
        )
        await self.log_event(channel.guild, "typing", description)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        if reaction.message.guild is None:  # Ignore DMs
            return
        description = (
            f"**User:** {user.name} ({user.mention})\n"
            f"**User ID:** `{user.id}`\n"
            f"**Message ID:** `{reaction.message.id}`\n"
            f"**Channel:** {reaction.message.channel.name}\n"
            f"**Channel ID:** `{reaction.message.channel.id}`\n"
            f"**Guild:** ||{reaction.message.guild.name} ({reaction.message.guild.id})||\n"
            f"**Emoji:** {reaction.emoji}\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(reaction.message.guild, "reaction_add", description)

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction: discord.Reaction, user: discord.User):
        if reaction.message.guild is None:  # Ignore DMs
            return
        description = (
            f"**User:** {user.name} ({user.mention})\n"
            f"**User ID:** `{user.id}`\n"
            f"**Message ID:** `{reaction.message.id}`\n"
            f"**Channel:** {reaction.message.channel.name}\n"
            f"**Channel ID:** `{reaction.message.channel.id}`\n"
            f"**Guild:** ||{reaction.message.guild.name} ({reaction.message.guild.id})||\n"
            f"**Emoji:** {reaction.emoji}\n"
            f"**Timestamp:** <t:{int(datetime.utcnow().timestamp())}:F>"
        )
        await self.log_event(reaction.message.guild, "reaction_remove", description)
