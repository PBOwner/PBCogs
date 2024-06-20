import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
import asyncio
from datetime import datetime

class RequestGB(commands.Cog):
    """Cog for handling global ban requests."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        default_global = {
            "requests": {},
            "notification_channel": None,
            "log_channels": {},
            "last_request_id": 0
        }
        self.config.register_global(**default_global)

    @commands.is_owner()
    @commands.command()
    async def setrequestchannel(self, ctx, channel: discord.TextChannel):
        """Set the channel for global ban notifications."""
        await self.config.notification_channel.set(channel.id)
        embed = discord.Embed(
            title="Notification Channel Set",
            description=f"Notification channel set to {channel.mention}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.is_owner()
    @commands.command()
    async def setlogging(self, ctx, channel: discord.TextChannel):
        """Set the log channel for global ban approvals."""
        async with self.config.log_channels() as log_channels:
            log_channels[str(ctx.guild.id)] = channel.id
        embed = discord.Embed(
            title="Log Channel Set",
            description=f"Log channel set to {channel.mention} for this server.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=["reqgb", "rgb"])
    async def reqglobalban(self, ctx, user_id: int, *, reason: str):
        """Request a global ban for a user."""
        notification_channel_id = await self.config.notification_channel()
        if not notification_channel_id:
            embed = discord.Embed(
                title="Error",
                description="Notification channel is not set. Please set it using the setrequestchannel command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        notification_channel = self.bot.get_channel(notification_channel_id)
        if not notification_channel:
            embed = discord.Embed(
                title="Error",
                description="Notification channel not found. Please set it again using the setrequestchannel command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        last_request_id = await self.config.last_request_id()
        request_id = last_request_id + 1
        await self.config.last_request_id.set(request_id)

        request = {
            "requester": ctx.author.id,
            "user_id": user_id,
            "reason": reason,
            "status": "Pending",
            "message_id": None
        }
        async with self.config.requests() as requests:
            requests[request_id] = request

        user = self.bot.get_user(user_id)
        if not user:
            try:
                user = await self.bot.fetch_user(user_id)
            except discord.NotFound:
                embed = discord.Embed(
                    title="Error",
                    description=f"User with ID {user_id} not found.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

        embed = discord.Embed(
            title="Global Ban Request",
            description=f"{ctx.author} has requested that user {user.display_name} ({user.id}) be globally banned.",
            color=discord.Color(0x00f0ff)
        )
        embed.add_field(name="Reason", value=reason, inline=True)
        embed.add_field(name="Status", value="Pending", inline=True)

        try:
            message = await notification_channel.send(embed=embed)
            request["message_id"] = message.id
            async with self.config.requests() as requests:
                requests[request_id] = request

            embed = discord.Embed(
                title="Request Sent",
                description=f"Global ban request for user {user.display_name} ({user.id}) has been sent to the notification channel.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(
                title="Error",
                description="Could not send a message to the notification channel. Please ensure the bot has permission to send messages in the channel.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.is_owner()
    @commands.command()
    async def approvereq(self, ctx, user_id: int):
        """Approve a global ban request."""
        async with self.config.requests() as requests:
            request = next((req for req in requests.values() if req["user_id"] == user_id and req["status"] == "Pending"), None)
            if not request:
                embed = discord.Embed(
                    title="Error",
                    description=f"No pending request found for user ID: {user_id}",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

            reason = request["reason"]
            user = self.bot.get_user(request["user_id"])
            if not user:
                try:
                    user = await self.bot.fetch_user(request["user_id"])
                except discord.NotFound:
                    embed = discord.Embed(
                        title="Error",
                        description=f"User with ID {request['user_id']} not found.",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=embed)
                    return

            if user:
                for guild in self.bot.guilds:
                    try:
                        await guild.ban(user, reason=reason)
                    except discord.Forbidden:
                        embed = discord.Embed(
                            title="Error",
                            description=f"Failed to ban {user.display_name} ({user.id}) in {guild.name} due to insufficient permissions.",
                            color=discord.Color.red()
                        )
                        await ctx.send(embed=embed)
                        continue
                    except discord.HTTPException as e:
                        embed = discord.Embed(
                            title="Error",
                            description=f"Failed to ban {user.display_name} ({user.id}) in {guild.name} due to an HTTP error: {e}",
                            color=discord.Color.red()
                        )
                        await ctx.send(embed=embed)
                        continue

                request["status"] = "Approved"
                requester = self.bot.get_user(request["requester"])
                if requester:
                    try:
                        await requester.send(embed=discord.Embed(
                            title="Request Approved",
                            description=f"Your request to globally ban {user.display_name} ({user.id}) was approved for {reason}.",
                            color=discord.Color.green()
                        ))
                    except discord.Forbidden:
                        pass

                notification_channel = self.bot.get_channel(await self.config.notification_channel())
                if notification_channel and request["message_id"]:
                    try:
                        message = await notification_channel.fetch_message(request["message_id"])
                        embed = discord.Embed(
                            title="Global Ban Request",
                            description=f"{requester} has requested that user {user.display_name} ({user.id}) be globally banned.",
                            color=discord.Color(0x008800)
                        )
                        embed.add_field(name="Reason", value=request["reason"], inline=True)
                        embed.add_field(name="Status", value="Approved", inline=True)
                        await message.edit(embed=embed)
                    except discord.Forbidden:
                        embed = discord.Embed(
                            title="Error",
                            description="Could not edit the message in the notification channel.",
                            color=discord.Color.red()
                        )
                        await ctx.send(embed=embed)
                    except discord.NotFound:
                        embed = discord.Embed(
                            title="Error",
                            description="Notification message not found.",
                            color=discord.Color.red()
                        )
                        await ctx.send(embed=embed)

                # Log the global ban in the log channels
                log_channels = await self.config.log_channels()
                for guild_id, channel_id in log_channels.items():
                    log_channel = self.bot.get_channel(channel_id)
                    if log_channel:
                        embed = discord.Embed(
                            title="New Globally Banned Member",
                            color=discord.Color.red(),
                            timestamp=datetime.utcnow()
                        )
                        embed.add_field(name="User", value=f"{user.display_name} ({user.id})", inline=False)
                        embed.add_field(name="Approved By", value=ctx.author.mention, inline=False)
                        embed.add_field(name="Reason", value=reason, inline=False)
                        embed.set_footer(text=f"Guild: {self.bot.get_guild(int(guild_id)).name}")
                        await log_channel.send(embed=embed)

                embed = discord.Embed(
                    title="Approved",
                    description=f"User {user.display_name} ({user.id}) has been banned from all servers.",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="Error",
                    description="User not found.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)

    @commands.is_owner()
    @commands.command()
    async def denyreq(self, ctx, user_id: int, *, deny_reason: str = None):
        """Deny a global ban request."""
        async with self.config.requests() as requests:
            request = next((req for req in requests.values() if req["user_id"] == user_id and req["status"] == "Pending"), None)
            if not request:
                embed = discord.Embed(
                    title="Error",
                    description=f"No pending request found for user ID: {user_id}",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

            original_reason = request["reason"]
            request["status"] = "Denied"
            requester = self.bot.get_user(request["requester"])
            user = self.bot.get_user(request["user_id"])
            if not user:
                try:
                    user = await self.bot.fetch_user(request["user_id"])
                except discord.NotFound:
                    embed = discord.Embed(
                        title="Error",
                        description=f"User with ID {request['user_id']} not found.",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=embed)
                    return

            if requester:
                try:
                    deny_message = f"Your request to globally ban {user.display_name} ({user.id}) was denied."
                    if deny_reason:
                        deny_message += f" Reason: {deny_reason}"
                    await requester.send(embed=discord.Embed(
                        title="Request Denied",
                        description=deny_message,
                        color=discord.Color.red()
                    ))
                except discord.Forbidden:
                    pass

            notification_channel = self.bot.get_channel(await self.config.notification_channel())
            if notification_channel and request["message_id"]:
                try:
                    message = await notification_channel.fetch_message(request["message_id"])
                    embed = discord.Embed(
                        title="Global Ban Request",
                        description=f"{requester} has requested that user {user.display_name} ({user.id}) be globally banned.",
                        color=discord.Color(0xff0000)
                    )
                    embed.add_field(name="Reason", value=original_reason, inline=True)
                    embed.add_field(name="Status", value="Denied", inline=True)
                    if deny_reason:
                        embed.add_field(name="Deny Reason", value=deny_reason, inline=True)
                    await message.edit(embed=embed)
                except discord.Forbidden:
                    embed = discord.Embed(
                        title="Error",
                        description="Could not edit the message in the notification channel.",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=embed)
                except discord.NotFound:
                    embed = discord.Embed(
                        title="Error",
                        description="Notification message not found.",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="Error",
                    description="Message ID not found in the request. Cannot update the notification message.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)

            embed = discord.Embed(
                title="Denied",
                description=f"Request for user {user.display_name} ({user.id}) has been denied.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

def setup(bot: Red):
    bot.add_cog(RequestGB(bot))
