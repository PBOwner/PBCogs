import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
from datetime import datetime

class AdvancedLogger(commands.Cog):
    """A cog for advanced logging of various actions in a server"""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "member_log_channel": None,
            "role_log_channel": None,
            "message_log_channel": None,
            "channel_log_channel": None,
            "webhook_log_channel": None,
            "app_log_channel": None,
            "voice_log_channel": None,
            "reaction_log_channel": None,
            "emoji_log_channel": None,
            "kick_log_channel": None,
            "ban_log_channel": None,
            "mute_log_channel": None,
            "timeout_log_channel": None,
        }
        default_global = {
            "command_log_channel": None,
            "error_log_channel": None,
        }
        self.config.register_guild(**default_guild)
        self.config.register_global(**default_global)

    async def log_event(self, guild: discord.Guild, log_type: str, title: str, description: str, color: discord.Color = discord.Color.blue(), author: discord.Member = None):
        try:
            if log_type in ["command", "error"]:
                log_channel_id = await self.config.get_raw(log_type + "_log_channel")
            else:
                log_channel_id = await self.config.guild(guild).get_raw(log_type + "_log_channel")

            if log_channel_id:
                log_channel = self.bot.get_channel(log_channel_id)
                if log_channel:
                    embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.utcnow())
                    if author:
                        embed.set_thumbnail(url=author.avatar_url)
                    await log_channel.send(embed=embed)
        except Exception as e:
            print(f"Failed to log event: {e}")

    async def log_global_event(self, log_type: str, title: str, description: str, color: discord.Color = discord.Color.blue(), author: discord.Member = None):
        try:
            log_channel_id = await self.config.get_raw(log_type + "_log_channel")
            if log_channel_id:
                log_channel = self.bot.get_channel(log_channel_id)
                if log_channel:
                    embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.utcnow())
                    if author:
                        embed.set_thumbnail(url=author.avatar_url)
                    await log_channel.send(embed=embed)
        except Exception as e:
            print(f"Failed to log global event: {e}")

    @commands.group()
    @commands.admin_or_permissions(manage_guild=True)
    async def logging(self, ctx):
        """Manage logging settings for various events in the server."""
        pass

    @logging.command()
    async def setchannel(self, ctx, log_type: str, channel: discord.TextChannel):
        """Set the channel for logging events.

        **Valid log types**: member, role, message, channel, webhook, app, voice, reaction, emoji, kick, ban, mute, timeout

        **Example**:
        `[p]logging setchannel member #member-log`
        `[p]logging setchannel role #role-log`
        `[p]logging setchannel message #message-log`
        `[p]logging setchannel channel #channel-log`
        `[p]logging setchannel webhook #webhook-log`
        `[p]logging setchannel app #app-log`
        `[p]logging setchannel voice #voice-log`
        `[p]logging setchannel reaction #reaction-log`
        `[p]logging setchannel emoji #emoji-log`
        `[p]logging setchannel kick #kick-log`
        `[p]logging setchannel ban #ban-log`
        `[p]logging setchannel mute #mute-log`
        `[p]logging setchannel timeout #timeout-log`
        """
        valid_log_types = ["member", "role", "message", "channel", "webhook", "app", "voice", "reaction", "emoji", "kick", "ban", "mute", "timeout"]
        if log_type not in valid_log_types:
            await ctx.send(f"Invalid log type. Valid log types are: {', '.join(valid_log_types)}")
            return
        await self.config.guild(ctx.guild).set_raw(log_type + "_log_channel", value=channel.id)
        await ctx.send(f"{log_type.capitalize()} logging channel set to {channel.mention}")

    @logging.command()
    async def removechannel(self, ctx, log_type: str):
        """Remove the logging channel.

        **Valid log types**: member, role, message, channel, webhook, app, voice, reaction, emoji, kick, ban, mute, timeout

        **Example**:
        `[p]logging removechannel member`
        `[p]logging removechannel role`
        `[p]logging removechannel message`
        `[p]logging removechannel channel`
        `[p]logging removechannel webhook`
        `[p]logging removechannel app`
        `[p]logging removechannel voice`
        `[p]logging removechannel reaction`
        `[p]logging removechannel emoji`
        `[p]logging removechannel kick`
        `[p]logging removechannel ban`
        `[p]logging removechannel mute`
        `[p]logging removechannel timeout`
        """
        valid_log_types = ["member", "role", "message", "channel", "webhook", "app", "voice", "reaction", "emoji", "kick", "ban", "mute", "timeout"]
        if log_type not in valid_log_types:
            await ctx.send(f"Invalid log type. Valid log types are: {', '.join(valid_log_types)}")
            return
        await self.config.guild(ctx.guild).set_raw(log_type + "_log_channel", value=None)
        await ctx.send(f"{log_type.capitalize()} logging channel removed")

    @logging.command()
    @commands.is_owner()
    async def setglobalchannel(self, ctx, log_type: str, channel: discord.TextChannel):
        """Set the global channel for logging commands and errors.

        **Valid log types**: command, error

        **Example**:
        `[p]logging setglobalchannel command #command-log`
        `[p]logging setglobalchannel error #error-log`
        """
        valid_log_types = ["command", "error"]
        if log_type not in valid_log_types:
            await ctx.send(f"Invalid log type. Valid log types are: {', '.join(valid_log_types)}")
            return
        await self.config.set_raw(log_type + "_log_channel", value=channel.id)
        await ctx.send(f"{log_type.capitalize()} logging channel set to {channel.mention}")

    @logging.command()
    @commands.is_owner()
    async def removeglobalchannel(self, ctx, log_type: str):
        """Remove the global logging channel for commands and errors.

        **Valid log types**: command, error

        **Example**:
        `[p]logging removeglobalchannel command`
        `[p]logging removeglobalchannel error`
        """
        valid_log_types = ["command", "error"]
        if log_type not in valid_log_types:
            await ctx.send(f"Invalid log type. Valid log types are: {', '.join(valid_log_types)}")
            return
        await self.config.set_raw(log_type + "_log_channel", value=None)
        await ctx.send(f"{log_type.capitalize()} logging channel removed")

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot:
            return
        if before.content != after.content:
            guild = before.guild
            description = (
                f"**Message Edited in {before.channel.mention}**\n"
                f"**Before:** {before.content}\n"
                f"**After:** {after.content}\n"
                f"**Author:** {before.author.mention}"
            )
            await self.log_event(guild, "message", "Message Edited", description, discord.Color.orange(), before.author)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        guild = message.guild
        description = (
            f"**Message Deleted in {message.channel.mention}**\n"
            f"**Content:** {message.content}\n"
            f"**Author:** {message.author.mention}"
        )
        await self.log_event(guild, "message", "Message Deleted", description, discord.Color.red(), message.author)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        description = f"**Member Joined:** {member.mention} ({member})"
        await self.log_event(guild, "member", "Member Joined", description, discord.Color.green(), member)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild = member.guild
        description = f"**Member Left:** {member.mention} ({member})"
        await self.log_event(guild, "member", "Member Left", description, discord.Color.red(), member)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        description = f"**Member Banned:** {user.mention} ({user})"
        await self.log_event(guild, "ban", "Member Banned", description, discord.Color.red(), user)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        description = f"**Member Unbanned:** {user.mention} ({user})"
        await self.log_event(guild, "ban", "Member Unbanned", description, discord.Color.green(), user)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.roles != after.roles:
            guild = before.guild
            added_roles = [role for role in after.roles if role not in before.roles]
            removed_roles = [role for role in before.roles if role not in after.roles]
            description = f"**Roles Updated for {before.mention} ({before}):**\n"
            if added_roles:
                description += f"**Roles Added:** {', '.join(role.mention for role in added_roles)}\n"
            if removed_roles:
                description += f"**Roles Removed:** {', '.join(role.mention for role in removed_roles)}\n"
            await self.log_event(guild, "role", "Roles Updated", description, discord.Color.blue(), before)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        guild = role.guild
        description = f"**Role Created:** {role.mention} ({role.name})"
        await self.log_event(guild, "role", "Role Created", description, discord.Color.green())

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        guild = role.guild
        description = f"**Role Deleted:** {role.name}"
        await self.log_event(guild, "role", "Role Deleted", description, discord.Color.red())

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        if before.name != after.name:
            guild = before.guild
            description = f"**Role Renamed:** {before.name} -> {after.name}"
            await self.log_event(guild, "role", "Role Renamed", description, discord.Color.blue())

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        guild = channel.guild
        description = f"**Channel Created:** {channel.mention} ({channel.name})"
        await self.log_event(guild, "channel", "Channel Created", description, discord.Color.green())

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        guild = channel.guild
        description = f"**Channel Deleted:** {channel.name}"
        await self.log_event(guild, "channel", "Channel Deleted", description, discord.Color.red())

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        if before.name != after.name:
            guild = before.guild
            description = f"**Channel Renamed:** {before.name} -> {after.name}"
            await self.log_event(guild, "channel", "Channel Renamed", description, discord.Color.blue())

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel):
        guild = channel.guild
        description = f"**Webhooks Updated in Channel:** {channel.mention} ({channel.name})"
        await self.log_event(guild, "webhook", "Webhooks Updated", description, discord.Color.blue())

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        if before.name != after.name:
            guild = before
            description = f"**Guild Renamed:** {before.name} -> {after.name}"
            await self.log_event(guild, "channel", "Guild Renamed", description, discord.Color.blue())

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        guild = member.guild
        if before.channel != after.channel:
            if before.channel is None:
                description = f"**{member.mention} joined voice channel:** {after.channel.mention}"
                await self.log_event(guild, "voice", "Voice Channel Join", description, discord.Color.green(), member)
            elif after.channel is None:
                description = f"**{member.mention} left voice channel:** {before.channel.mention}"
                await self.log_event(guild, "voice", "Voice Channel Leave", description, discord.Color.red(), member)
            else:
                description = f"**{member.mention} switched voice channel:** {before.channel.mention} -> {after.channel.mention}"
                await self.log_event(guild, "voice", "Voice Channel Switch", description, discord.Color.blue(), member)

        if before.self_mute != after.self_mute:
            if after.self_mute:
                description = f"**{member.mention} muted themselves in voice channel:** {after.channel.mention}"
                await self.log_event(guild, "voice", "Voice Channel Self Mute", description, discord.Color.orange(), member)
            else:
                description = f"**{member.mention} unmuted themselves in voice channel:** {after.channel.mention}"
                await self.log_event(guild, "voice", "Voice Channel Self Unmute", description, discord.Color.green(), member)

        if before.self_deaf != after.self_deaf:
            if after.self_deaf:
                description = f"**{member.mention} deafened themselves in voice channel:** {after.channel.mention}"
                await self.log_event(guild, "voice", "Voice Channel Self Deafen", description, discord.Color.orange(), member)
            else:
                description = f"**{member.mention} undeafened themselves in voice channel:** {after.channel.mention}"
                await self.log_event(guild, "voice", "Voice Channel Self Undeafen", description, discord.Color.green(), member)

        if before.mute != after.mute:
            if after.mute:
                description = f"**{member.mention} was server muted in voice channel:** {after.channel.mention}"
                await self.log_event(guild, "voice", "Voice Channel Server Mute", description, discord.Color.red(), member)
            else:
                description = f"**{member.mention} was server unmuted in voice channel:** {after.channel.mention}"
                await self.log_event(guild, "voice", "Voice Channel Server Unmute", description, discord.Color.green(), member)

        if before.deaf != after.deaf:
            if after.deaf:
                description = f"**{member.mention} was server deafened in voice channel:** {after.channel.mention}"
                await self.log_event(guild, "voice", "Voice Channel Server Deafen", description, discord.Color.red(), member)
            else:
                description = f"**{member.mention} was server undeafened in voice channel:** {after.channel.mention}"
                await self.log_event(guild, "voice", "Voice Channel Server Undeafen", description, discord.Color.green(), member)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return
        guild = reaction.message.guild
        description = f"**Reaction Added:** {reaction.emoji}\n**Message:** [Jump to Message]({reaction.message.jump_url})\n**User:** {user.mention}"
        await self.log_event(guild, "reaction", "Reaction Added", description, discord.Color.green(), user)

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        if user.bot:
            return
        guild = reaction.message.guild
        description = f"**Reaction Removed:** {reaction.emoji}\n**Message:** [Jump to Message]({reaction.message.jump_url})\n**User:** {user.mention}"
        await self.log_event(guild, "reaction", "Reaction Removed", description, discord.Color.red(), user)

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        before_emojis = set(before)
        after_emojis = set(after)
        added_emojis = after_emojis - before_emojis
        removed_emojis = before_emojis - after_emojis
        updated_emojis = {emoji for emoji in before_emojis & after_emojis if emoji.name != next(e.name for e in after if e.id == emoji.id)}

        for emoji in added_emojis:
            description = f"**Emoji Added:** {emoji} ({emoji.name})"
            await self.log_event(guild, "emoji", "Emoji Added", description, discord.Color.green())

        for emoji in removed_emojis:
            description = f"**Emoji Removed:** {emoji} ({emoji.name})"
            await self.log_event(guild, "emoji", "Emoji Removed", description, discord.Color.red())

        for emoji in updated_emojis:
            description = f"**Emoji Updated:** {emoji} ({emoji.name})"
            await self.log_event(guild, "emoji", "Emoji Updated", description, discord.Color.blue())

    @commands.Cog.listener()
    async def on_command(self, ctx):
        description = f"**Command Executed:** {ctx.command}\n**User:** {ctx.author.mention}\n**Channel:** {ctx.channel.mention}\n**Message:** {ctx.message.content}"
        await self.log_global_event("command", "Command Executed", description, discord.Color.purple(), ctx.author)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        description = f"**Command Error:** {ctx.command}\n**User:** {ctx.author.mention}\n**Channel:** {ctx.channel.mention}\n**Message:** {ctx.message.content}\n**Error:** {error}"
        await self.log_global_event("error", "Command Error", description, discord.Color.red(), ctx.author)

    @commands.Cog.listener()
    async def on_member_kick(self, guild, user):
        description = f"**Member Kicked:** {user.mention} ({user})"
        await self.log_event(guild, "kick", "Member Kicked", description, discord.Color.red(), user)

    @commands.Cog.listener()
    async def on_member_mute(self, guild, user):
        description = f"**Member Muted:** {user.mention} ({user})"
        await self.log_event(guild, "mute", "Member Muted", description, discord.Color.red(), user)

    @commands.Cog.listener()
    async def on_member_timeout(self, guild, user):
        description = f"**Member Timed Out:** {user.mention} ({user})"
        await self.log_event(guild, "timeout", "Member Timed Out", description, discord.Color.red(), user)
