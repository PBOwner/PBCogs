import discord
from redbot.core import commands, Config
from redbot.core.bot import Red

class RequestGB(commands.Cog):
    """Cog for handling global ban requests."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        default_global = {
            "requests": {}
        }
        self.config.register_global(**default_global)

    @commands.command()
    async def reqglobalban(self, ctx, user_id: int, *, reason: str):
        """Request a global ban for a user."""
        bot_owner = (await self.bot.application_info()).owner
        request_id = len(await self.config.requests()) + 1
        request = {
            "requester": ctx.author.id,
            "user_id": user_id,
            "reason": reason,
            "status": "pending"
        }
        async with self.config.requests() as requests:
            requests[request_id] = request
        await bot_owner.send(f"{ctx.author} has requested that user with ID {user_id} be global banned for the reason: {reason}")
        await ctx.send(f"Global ban request for user ID {user_id} has been sent to the bot owner.")

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
                    await requester.send("Globalban was approved.")
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
                await requester.send("Globalban was denied.")
            await ctx.send(f"Request {request_id} has been denied.")

def setup(bot: Red):
    bot.add_cog(RequestGB(bot))
