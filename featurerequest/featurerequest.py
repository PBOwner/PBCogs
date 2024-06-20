import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
from typing import Optional

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

    @commands.is_owner()
    @commands.command()
    async def frchannel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the channel for feature requests."""
        await self.config.request_channel.set(channel.id)
        await ctx.send(f"Request channel set to: {channel.mention}")

    @commands.command()
    async def frequest(self, ctx: commands.Context, *, feature: str):
        """Request a new feature for bot.name."""
        request_channel_id = await self.config.request_channel()
        if not request_channel_id:
            await ctx.send("Request channel is not set. Please ask the bot owner to set it using the frchannel command.")
            return

        request_channel = self.bot.get_channel(request_channel_id)
        if not request_channel:
            await ctx.send("Request channel not found. Please ask the bot owner to set it again using the frchannel command.")
            return

        request_id = len(await self.config.requests()) + 1
        request_data = {
            "requester_id": ctx.author.id,
            "feature": feature,
            "status": "pending"
        }

        async with self.config.requests() as requests:
            requests[request_id] = request_data

        embed = discord.Embed(
            title="Feature Request",
            description=f"Feature requested by {ctx.author.mention}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Feature", value=feature, inline=False)
        embed.add_field(name="Status", value="Pending", inline=False)

        await request_channel.send(embed=embed)
        await ctx.send("Your feature request has been submitted.")

    @commands.is_owner()
    @commands.command()
    async def acceptfr(self, ctx: commands.Context, request_id: int):
        """Accept a feature request."""
        async with self.config.requests() as requests:
            request_data = requests.get(request_id)
            if not request_data:
                await ctx.send(f"No feature request found with ID: {request_id}")
                return

            if request_data["status"] != "pending":
                await ctx.send(f"Feature request {request_id} has already been processed.")
                return

            request_data["status"] = "accepted"
            requester = self.bot.get_user(request_data["requester_id"])
            if requester:
                try:
                    await requester.send(embed=discord.Embed(
                        title="Feature Request Accepted",
                        description=f"Your feature request has been accepted.",
                        color=discord.Color.green()
                    ))
                except discord.Forbidden:
                    pass

            await ctx.send(f"Feature request {request_id} has been accepted.")

    @commands.is_owner()
    @commands.command()
    async def denyfr(self, ctx: commands.Context, request_id: int):
        """Deny a feature request."""
        async with self.config.requests() as requests:
            request_data = requests.get(request_id)
            if not request_data:
                await ctx.send(f"No feature request found with ID: {request_id}")
                return

            if request_data["status"] != "pending":
                await ctx.send(f"Feature request {request_id} has already been processed.")
                return

            request_data["status"] = "denied"
            requester = self.bot.get_user(request_data["requester_id"])
            if requester:
                try:
                    await requester.send(embed=discord.Embed(
                        title="Feature Request Denied",
                        description=f"Your feature request has been denied.",
                        color=discord.Color.red()
                    ))
                except discord.Forbidden:
                    pass

            await ctx.send(f"Feature request {request_id} has been denied.")

def setup(bot: Red):
    bot.add_cog(FeatureRequest(bot))
