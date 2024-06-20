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
        await ctx.send(f"Notification channel set to {channel.mention}")

    @commands.command()
    async def reqglobalban(self, ctx, user_id: int, *, reason: str):
        """Request a global ban for a user."""
        notification_channel_id = await self.config.notification_channel()
        if not notification_channel_id:
            await ctx.send("Notification channel is not set. Please set it using the setrequestchannel command.")
            return

        notification_channel = self.bot.get_channel(notification_channel_id)
        if not notification_channel:
            await ctx.send("Notification channel not found. Please set it again using the setrequestchannel command.")
            return

        async with self.config.last_request_id() as last_request_id:
            request_id = last_request_id + 1
            await self.config.last_request_id.set(request_id)

        request = {
            "requester": ctx.author.id,
            "user_id": user_id,
            "reason": reason,
            "status": "pending"
        }
        async with self.config.requests() as requests:
            requests[request_id] = request

        embed = discord.Embed(
            title="Global Ban Request",
            description=f"{ctx.author} has requested that user with ID {user_id} be global banned.",
            color=discord.Color.red()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text=f"Request ID: {request_id}")

        try:
            await notification_channel.send(embed=embed)
            await ctx.send(f"Global ban request for user ID {user_id} has been sent to the notification channel.")
        except discord.Forbidden:
            await ctx.send("Could not send a message to the notification channel. Please ensure the bot has permission to send messages in the channel.")

    @commands.is_owner()
    @commands.command()
    async def approvereq(self, ctx, request_id: int):
        """Approve a global ban request."""
        async with self.config.requests() as requests:
            if request_id not in requests:
                await ctx.send("Invalid request ID.")
                return
            request = requests[request_id]
            if request["status"] != "pending":
                await ctx.send("This request has already been processed.")
                return
            user = self.bot.get_user(request["user_id"])
            if user:
                for guild in self.bot.guilds:
                    try:
                        await guild.ban(user, reason=request["reason"])
                    except discord.Forbidden:
                        await ctx.send(f"Failed to ban {user} in {guild.name} due to insufficient permissions.")
                    except discord.HTTPException as e:
                        await ctx.send(f"Failed to ban {user} in {guild.name} due to an HTTP error: {e}")
                request["status"] = "approved"
                requester = self.bot.get_user(request["requester"])
                if requester:
                    try:
                        await requester.send("Globalban was approved.")
                    except discord.Forbidden:
                        await ctx.send("Could not send a DM to the requester to inform them of the approval.")
                await ctx.send(f"User {user} has been banned from all servers.")
            else:
                await ctx.send("User not found.")

    @commands.is_owner()
    @commands.command()
    async def denyreq(self, ctx, request_id: int):
        """Deny a global ban request."""
        async with self.config.requests() as requests:
            if request_id not in requests:
                await ctx.send("Invalid request ID.")
                return
            request = requests[request_id]
            if request["status"] != "pending":
                await ctx.send("This request has already been processed.")
                return
            request["status"] = "denied"
            requester = self.bot.get_user(request["requester"])
            if requester:
                try:
                    await requester.send("Globalban was denied.")
                except discord.Forbidden:
                    await ctx.send("Could not send a DM to the requester to inform them of the denial.")
            await ctx.send(f"Request {request_id} has been denied.")

def setup(bot: Red):
    bot.add_cog(RequestGB(bot))
