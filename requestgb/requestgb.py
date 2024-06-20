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
            await message.add_reaction("✅")  # Approve
            await message.add_reaction("❌")  # Deny
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

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Handle reactions to approve or deny global ban requests."""
        if payload.user_id == self.bot.user.id:
            return

        notification_channel_id = await self.config.notification_channel()
        if payload.channel_id != notification_channel_id:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        channel = guild.get_channel(payload.channel_id)
        if not channel:
            return

        message = await channel.fetch_message(payload.message_id)
        if not message:
            return

        emoji = str(payload.emoji)
        if emoji not in ["✅", "❌"]:
            return

        async with self.config.requests() as requests:
            for request_id, request in requests.items():
                if request["message_id"] == payload.message_id:
                    if request["status"] != "pending":
                        return

                    user = self.bot.get_user(request["user_id"])
                    requester = self.bot.get_user(request["requester"])

                    if emoji == "✅":
                        # Approve the request
                        if user:
                            for guild in self.bot.guilds:
                                try:
                                    await guild.ban(user, reason=request["reason"])
                                except discord.Forbidden:
                                    continue
                                except discord.HTTPException:
                                    continue

                        request["status"] = "approved"
                        embed = discord.Embed(
                            title="Global Ban Request: Approved",
                            description=f"{requester} has requested that user with ID {request['user_id']} be global banned.",
                            color=discord.Color(0x008800)
                        )
                        embed.add_field(name="Reason", value=request["reason"], inline=False)
                        embed.set_footer(text=f"Request ID: {request_id}")
                        await message.edit(embed=embed)
                        await message.clear_reactions()

                        if requester:
                            try:
                                await requester.send(embed=discord.Embed(
                                    title="Request Approved",
                                    description=f"Your request for {request['user_id']} was approved.",
                                    color=discord.Color.green()
                                ))
                            except discord.Forbidden:
                                pass

                    elif emoji == "❌":
                        # Deny the request
                        request["status"] = "denied"
                        embed = discord.Embed(
                            title="Global Ban Request: Denied",
                            description=f"{requester} has requested that user with ID {request['user_id']} be global banned.",
                            color=discord.Color(0xff0000)
                        )
                        embed.add_field(name="Reason", value=request["reason"], inline=False)
                        embed.set_footer(text=f"Request ID: {request_id}")
                        await message.edit(embed=embed)
                        await message.clear_reactions()

                        if requester:
                            try:
                                await requester.send(embed=discord.Embed(
                                    title="Request Denied",
                                    description=f"Your request for {request['user_id']} was denied.",
                                    color=discord.Color.red()
                                ))
                            except discord.Forbidden:
                                pass

                    break

def setup(bot: Red):
    bot.add_cog(RequestGB(bot))
