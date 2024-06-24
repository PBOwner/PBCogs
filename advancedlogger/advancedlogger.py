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
        }
        default_global = {
            "command_log_channel": None,
            "error_log_channel": None,
        }
        self.config.register_guild(**default_guild)
        self.config.register_global(**default_global)

    async def log_event(self, guild: discord.Guild, log_type: str, title: str, description: str, color: discord.Color = discord.Color.blue()):
        if log_type in ["command", "error"]:
            log_channel_id = await self.config.get_raw(log_type + "_log_channel")
        else:
            log_channel_id = await self.config.guild(guild).get_raw(log_type + "_log_channel")

        if log_channel_id:
            log_channel = self.bot.get_channel(log_channel_id)
            if log_channel:
                embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.utcnow())
                await log_channel.send(embed=embed)

    @commands.group()
    @commands.admin_or_permissions(manage_guild=True)
    async def logging(self, ctx):
        """Group command for managing logging settings"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @logging.command()
    async def setchannel(self, ctx, log_type: str, channel: discord.TextChannel):
        """Set the channel for logging events"""
        valid_log_types = ["member", "role", "message", "channel", "webhook", "app"]
        if log_type not in valid_log_types:
            await ctx.send(f"Invalid log type. Valid log types are: {', '.join(valid_log_types)}")
            return
        await self.config.guild(ctx.guild).set_raw(log_type + "_log_channel", value=channel.id)
        await ctx.send(f"{log_type.capitalize()} logging channel set to {channel.mention}")

    @logging.command()
    async def removechannel(self, ctx, log_type: str):
        """Remove the logging channel"""
        valid_log_types = ["member", "role", "message", "channel", "webhook", "app"]
        if log_type not in valid_log_types:
            await ctx.send(f"Invalid log type. Valid log types are: {', '.join(valid_log_types)}")
            return
        await self.config.guild(ctx.guild).set_raw(log_type + "_log_channel", value=None)
        await ctx.send(f"{log_type.capitalize()} logging channel removed")

    @logging.command()
    @commands.is_owner()
    async def setglobalchannel(self, ctx, log_type: str, channel: discord.TextChannel):
        """Set the global channel for logging commands and errors"""
        valid_log_types = ["command", "error"]
        if log_type not in valid_log_types:
            await ctx.send(f"Invalid log type. Valid log types are: {', '.join(valid_log_types)}")
            return
        await self.config.set_raw(log_type + "_log_channel", value=channel.id)
        await ctx.send(f"{log_type.capitalize()} logging channel set to {channel.mention}")

    @logging.command()
    @commands.is_owner()
    async def removeglobalchannel(self, ctx, log_type: str):
        """Remove the global logging channel for commands and errors"""
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
            await self.log_event(guild, "message", "Message Edited", description, discord.Color.orange())

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
        await self.log_event(guild, "message", "Message Deleted", description, discord.Color.red())

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        description = f"**Member Joined:** {member.mention} ({member})"
        await self.log_event(guild, "member", "Member Joined", description, discord.Color.green())

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild = member.guild
        description = f"**Member Left:** {member.mention} ({member})"
        await self.log_event(guild, "member", "Member Left", description, discord.Color.red())

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        description = f"**Member Banned:** {user.mention} ({user})"
        await self.log_event(guild, "member", "Member Banned", description, discord.Color.red())

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        description = f"**Member Unbanned:** {user.mention} ({user})"
        await self.log_event(guild, "member", "Member Unbanned", description, discord.Color.green())

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
            await self.log_event(guild, "role", "Roles Updated", description, discord.Color.blue())

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
            description = f"**Guild Renamed:** {before.name} -> {after.name}"
            await self.log_event(before, "channel", "Guild Renamed", description, discord.Color.blue())

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.bot != after.bot:
            guild = before.guild
            description = f"**Bot Status Changed:** {before.mention} ({before}) -> {after.mention} ({after})"
            await self.log_event(guild, "app", "Bot Status Changed", description, discord.Color.blue())

    @commands.Cog.listener()
    async def on_command(self, ctx):
        guild = ctx.guild
        description = f"**Command Executed:** {ctx.command}\n**User:** {ctx.author.mention}\n**Channel:** {ctx.channel.mention}\n**Message:** {ctx.message.content}"
        await self.log_event(guild, "command", "Command Executed", description, discord.Color.purple())

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        guild = ctx.guild
        description = f"**Command Error:** {ctx.command}\n**User:** {ctx.author.mention}\n**Channel:** {ctx.channel.mention}\n**Message:** {ctx.message.content}\n**Error:** {error}"
        await self.log_event(guild, "error", "Command Error", description, discord.Color.red())

def setup(bot):
    bot.add_cog(AdvancedLogger(bot))
