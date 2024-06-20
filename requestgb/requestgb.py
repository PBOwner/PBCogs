import discord
from redbot.core import commands, Config
from redbot.core.bot import Red

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

    @commands.command()
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

        embed = discord.Embed(
            title="Global Ban Request: Pending",
            description=f"{ctx.author} has requested that user with ID {user_id} be global banned.",
            color=discord.Color(0x00f0ff)
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text=f"Request ID: {request_id}")

        try:
            message = await notification_channel.send(embed=embed)
            request["message_id"] = message.id
            async with self.config.requests() as requests:
                requests[request_id] = request

            embed = discord.Embed(
                title="Request Sent",
                description=f"Global ban request for user ID {user_id} has been sent to the notification channel.",
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
    async def approvereq(self, ctx, request_id: int):
        """Approve a global ban request."""
        async with self.config.requests() as requests:
            if request_id not in requests:
                embed = discord.Embed(
                    title="Error",
                    description="Invalid request ID.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            request = requests[request_id]
            if request["status"] != "pending":
                embed = discord.Embed(
                    title="Error",
                    description="This request has already been processed.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

            user = self.bot.get_user(request["user_id"])
            if user:
                for guild in self.bot.guilds:
                    try:
                        await guild.ban(user, reason=request["reason"])
                    except discord.Forbidden:
                        embed = discord.Embed(
                            title="Error",
                            description=f"Failed to ban {user} in {guild.name} due to insufficient permissions.",
                            color=discord.Color.red()
                        )
                        await ctx.send(embed=embed)
                        continue
                    except discord.HTTPException as e:
                        embed = discord.Embed(
                            title="Error",
                            description=f"Failed to ban {user} in {guild.name} due to an HTTP error: {e}",
                            color=discord.Color.red()
                        )
                        await ctx.send(embed=embed)
                        continue

                request["status"] = "approved"
                requester = self.bot.get_user(request["requester"])
                if requester:
                    try:
                        await requester.send("Globalban was approved.")
                    except discord.Forbidden:
                        embed = discord.Embed(
                            title="Error",
                            description="Could not send a DM to the requester to inform them of the approval.",
                            color=discord.Color.red()
                        )
                        await ctx.send(embed=embed)

                notification_channel = self.bot.get_channel(await self.config.notification_channel())
                if notification_channel:
                    try:
                        message = await notification_channel.fetch_message(request["message_id"])
                        embed = discord.Embed(
                            title="Global Ban Request: Approved",
                            description=f"{request['requester']} has requested that user with ID {request['user_id']} be global banned.",
                            color=discord.Color(0x008800)
                        )
                        embed.add_field(name="Reason", value=request["reason"], inline=False)
                        embed.set_footer(text=f"Request ID: {request_id}")
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
                    description=f"User {user} has been banned from all servers.",
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
    async def denyreq(self, ctx, request_id: int):
        """Deny a global ban request."""
        async with self.config.requests() as requests:
            if request_id not in requests:
                embed = discord.Embed(
                    title="Error",
                    description="Invalid request ID.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            request = requests[request_id]
            if request["status"] != "pending":
                embed = discord.Embed(
                    title="Error",
                    description="This request has already been processed.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

            request["status"] = "denied"
            requester = self.bot.get_user(request["requester"])
            if requester:
                try:
                    await requester.send("Globalban was denied.")
                except discord.Forbidden:
                    embed = discord.Embed(
                        title="Error",
                        description="Could not send a DM to the requester to inform them of the denial.",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=embed)

            notification_channel = self.bot.get_channel(await self.config.notification_channel())
            if notification_channel:
                try:
                    message = await notification_channel.fetch_message(request["message_id"])
                    embed = discord.Embed(
                        title="Global Ban Request: Denied",
                        description=f"{request['requester']} has requested that user with ID {request['user_id']} be global banned.",
                        color=discord.Color(0xff0000)
                    )
                    embed.add_field(name="Reason", value=request["reason"], inline=False)
                    embed.set_footer(text=f"Request ID: {request_id}")
                    await message.edit(embed=embed)
                except discord.Forbidden:
                    embed = discord.Embed(
                        title="Error",
                        description="Could not edit the message in the notification channel.",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=embed)

            embed = discord.Embed(
                title="Denied",
                description=f"Request {request_id} has been denied.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

def setup(bot: Red):
    bot.add_cog(RequestGB(bot))
