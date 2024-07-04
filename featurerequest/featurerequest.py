import discord
import uuid
from redbot.core import commands, Config
from redbot.core.bot import Red

class FeatureRequest(commands.Cog):
    """Cog to handle feature requests."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567892, force_registration=True)
        default_global = {
            "request_channel": None,
            "requests": {}
        }
        self.config.register_global(**default_global)

    @commands.group(aliases=["fr"])
    async def frequest(self, ctx: commands.Context):
        """Base command for feature requests."""
        pass

    @frequest.command()
    async def submit(self, ctx: commands.Context, *, feature: str):
        """Request a new feature for the bot."""
        request_channel_id = await self.config.request_channel()
        if not request_channel_id:
            await ctx.send("Request channel is not set. Please ask the bot owner to set it using the frequest channel command.")
            return

        request_channel = self.bot.get_channel(request_channel_id)
        if not request_channel:
            await ctx.send("Request channel not found. Please ask the bot owner to set it again using the frequest channel command.")
            return

        request_id = str(uuid.uuid4())
        embed = discord.Embed(
            title="Feature Request",
            description=f"Feature requested by {ctx.author.mention}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Feature", value=feature, inline=True)
        embed.add_field(name="Status", value="Pending", inline=True)
        embed.add_field(name="Request ID", value=request_id, inline=True)

        message = await request_channel.send(embed=embed)
        request_data = {
            "requester_id": ctx.author.id,
            "feature": feature,
            "status": "pending",
            "message_id": message.id,
            "request_id": request_id
        }

        async with self.config.requests() as requests:
            requests[request_id] = request_data

        await ctx.send(f"Your feature request has been successfully submitted! Your request ID is {request_id}")

    async def update_status(self, ctx: commands.Context, request_id: str, status: str, color: discord.Color, reason: str = None):
        async with self.config.requests() as requests:
            request_data = requests.get(request_id)
            if not request_data:
                await ctx.send(f"No feature request found with ID: {request_id}")
                return

            request_data["status"] = status
            requester = self.bot.get_user(request_data["requester_id"])
            if requester:
                description = f"Your feature request with ID `{request_id}` was {status}."
                if reason:
                    description += f"\n\n**Reason:** {reason}"
                try:
                    await requester.send(embed=discord.Embed(
                        title=f"Feature Request {status.capitalize()}",
                        description=description,
                        color=color
                    ))
                except discord.Forbidden:
                    pass

            request_channel = self.bot.get_channel(await self.config.request_channel())
            if request_channel:
                try:
                    message = await request_channel.fetch_message(request_data["message_id"])
                    embed = message.embeds[0]
                    embed.set_field_at(1, name="Status", value=status.capitalize(), inline=True)
                    embed.color = color
                    await message.edit(embed=embed)
                except discord.NotFound:
                    await ctx.send(f"Message with ID {request_data['message_id']} not found in the request channel.")
                except discord.Forbidden:
                    await ctx.send("I don't have permission to edit the message in the request channel.")

            await ctx.send(f"Feature request with ID `{request_id}` has been {status}.")

    @frequest.command()
    @commands.is_owner()
    async def accept(self, ctx: commands.Context, request_id: str, *, reason: str = None):
        """Accept a feature request."""
        await self.update_status(ctx, request_id, "accepted", discord.Color.green(), reason)

    @frequest.command()
    @commands.is_owner()
    async def deny(self, ctx: commands.Context, request_id: str, *, reason: str = None):
        """Deny a feature request."""
        await self.update_status(ctx, request_id, "denied", discord.Color.red(), reason)

    @frequest.command()
    @commands.is_owner()
    async def consider(self, ctx: commands.Context, request_id: str, *, reason: str = None):
        """Consider a feature request."""
        await self.update_status(ctx, request_id, "considering", discord.Color.blue(), reason)

    @frequest.command()
    async def status(self, ctx: commands.Context, request_id: str):
        """Check the status of a feature request."""
        async with self.config.requests() as requests:
            request_data = requests.get(request_id)
            if not request_data:
                await ctx.send(f"No feature request found with ID: {request_id}")
                return

            status = request_data["status"]
            await ctx.author.send(embed=discord.Embed(
                title="Feature Request Status",
                description=f"The request status is: **{status.capitalize()}**",
                color=discord.Color.blue()
            ))

    @frequest.command()
    @commands.is_owner()
    async def channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the channel for feature requests."""
        await self.config.request_channel.set(channel.id)
        await ctx.send(f"Request channel set to: {channel.mention}")

class SlashRequest(commands.Cog):
    """Cog to handle slash command feature requests."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567893, force_registration=True)
        default_global = {
            "request_channel": None,
            "requests": {}
        }
        self.config.register_global(**default_global)

    @commands.group(aliases=["sr"])
    async def srequest(self, ctx: commands.Context):
        """Base command for slash feature requests."""
        pass

    @srequest.command()
    async def submit(self, ctx: commands.Context, *, feature: str):
        """Request a new slash feature for the bot."""
        request_channel_id = await self.config.request_channel()
        if not request_channel_id:
            await ctx.send("Request channel is not set. Please ask the bot owner to set it using the srequest channel command.")
            return

        request_channel = self.bot.get_channel(request_channel_id)
        if not request_channel:
            await ctx.send("Request channel not found. Please ask the bot owner to set it again using the srequest channel command.")
            return

        request_id = str(uuid.uuid4())
        embed = discord.Embed(
            title="Slash Feature Request",
            description=f"Slash feature requested by {ctx.author.mention}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Feature", value=feature, inline=True)
        embed.add_field(name="Status", value="Pending", inline=True)
        embed.add_field(name="Request ID", value=request_id, inline=True)

        message = await request_channel.send(embed=embed)
        request_data = {
            "requester_id": ctx.author.id,
            "feature": feature,
            "status": "pending",
            "message_id": message.id,
            "request_id": request_id
        }

        async with self.config.requests() as requests:
            requests[request_id] = request_data

        await ctx.send(f"Your slash feature request has been successfully submitted! Your request ID is {request_id}")

    async def update_status(self, ctx: commands.Context, request_id: str, status: str, color: discord.Color, reason: str = None):
        async with self.config.requests() as requests:
            request_data = requests.get(request_id)
            if not request_data:
                await ctx.send(f"No slash feature request found with ID: {request_id}")
                return

            request_data["status"] = status
            requester = self.bot.get_user(request_data["requester_id"])
            if requester:
                description = f"Your slash feature request with ID `{request_id}` was {status}."
                if reason:
                    description += f"\n\n**Reason:** {reason}"
                try:
                    await requester.send(embed=discord.Embed(
                        title=f"Slash Feature Request {status.capitalize()}",
                        description=description,
                        color=color
                    ))
                except discord.Forbidden:
                    pass

            request_channel = self.bot.get_channel(await self.config.request_channel())
            if request_channel:
                try:
                    message = await request_channel.fetch_message(request_data["message_id"])
                    embed = message.embeds[0]
                    embed.set_field_at(1, name="Status", value=status.capitalize(), inline=True)
                    embed.color = color
                    await message.edit(embed=embed)
                except discord.NotFound:
                    await ctx.send(f"Message with ID {request_data['message_id']} not found in the request channel.")
                except discord.Forbidden:
                    await ctx.send("I don't have permission to edit the message in the request channel.")

            await ctx.send(f"Slash feature request with ID `{request_id}` has been {status}.")

    @srequest.command()
    @commands.is_owner()
    async def accept(self, ctx: commands.Context, request_id: str, *, reason: str = None):
        """Accept a slash feature request."""
        await self.update_status(ctx, request_id, "accepted", discord.Color.green(), reason)

    @srequest.command()
    @commands.is_owner()
    async def deny(self, ctx: commands.Context, request_id: str, *, reason: str = None):
        """Deny a slash feature request."""
        await self.update_status(ctx, request_id, "denied", discord.Color.red(), reason)

    @srequest.command()
    @commands.is_owner()
    async def consider(self, ctx: commands.Context, request_id: str, *, reason: str = None):
        """Consider a slash feature request."""
        await self.update_status(ctx, request_id, "considering", discord.Color.blue(), reason)

    @srequest.command()
    async def status(self, ctx: commands.Context, request_id: str):
        """Check the status of a slash feature request."""
        async with self.config.requests() as requests:
            request_data = requests.get(request_id)
            if not request_data:
                await ctx.send(f"No slash feature request found with ID: {request_id}")
                return

            status = request_data["status"]
            await ctx.author.send(embed=discord.Embed(
                title="Slash Feature Request Status",
                description=f"The request status is: **{status.capitalize()}**",
                color=discord.Color.blue()
            ))

    @srequest.command()
    @commands.is_owner()
    async def channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the channel for slash feature requests."""
        await self.config.request_channel.set(channel.id)
        await ctx.send(f"Request channel set to: {channel.mention}")

def setup(bot: Red):
    bot.add_cog(FeatureRequest(bot))
    bot.add_cog(SlashRequest(bot))
