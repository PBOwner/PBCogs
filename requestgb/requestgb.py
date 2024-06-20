import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
import asyncio

class RequestGB(commands.Cog):
    """Cog for handling global ban requests."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        default_global = {
            "requests": {},
            "notification_channel": None,
            "last_request_id": 0
        }
        self.config.register_global(**default_global)

    @commands.group(name="requestgb", aliases=["reqgb"], invoke_without_command=True)
    async def requestgb(self, ctx):
        """Base command for global ban requests."""
        await ctx.send_help(ctx.command)

    @requestgb.command()
    @commands.is_owner()
    async def setrequestchannel(self, ctx, channel: discord.TextChannel):
        """Set the channel for global ban notifications."""
        await self.config.notification_channel.set(channel.id)
        embed = discord.Embed(
            title="Notification Channel Set",
            description=f"Notification channel set to {channel.mention}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @requestgb.command()
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
            "status": "pending",
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

    @requestgb.command()
    @commands.is_owner()
    async def approvereq(self, ctx, user_id: int, *, reason: str):
        """Approve a global ban request."""
        async with self.config.requests() as requests:
            request = next((req for req in requests.values() if req["user_id"] == user_id and req["status"] == "pending"), None)
            if not request:
                embed = discord.Embed(
                    title="Error",
                    description=f"No pending request found for user ID: {user_id}",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

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

                request["status"] = "approved"
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

    @requestgb.command()
    @commands.is_owner()
    async def denyreq(self, ctx, user_id: int, *, reason: str):
        """Deny a global ban request."""
        async with self.config.requests() as requests:
            request = next((req for req in requests.values() if req["user_id"] == user_id and req["status"] == "pending"), None)
            if not request:
                embed = discord.Embed(
                    title="Error",
                    description=f"No pending request found for user ID: {user_id}",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

            request["status"] = "denied"
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
                    await requester.send(embed=discord.Embed(
                        title="Request Denied",
                        description=f"Your request to globally ban {user.display_name} ({user.id}) was denied for {reason}.",
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
                    embed.add_field(name="Reason", value=request["reason"], inline=True)
                    embed.add_field(name="Status", value="Denied", inline=True)
                    await message.edit(embed=embed)
                except discord.Forbidden:
                    embed = discord.Embed(
                        title="Error",
                        description="Could not edit the message in the notification channel.",
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
