import discord
from redbot.core import commands, Config
from discord.ext import tasks

class Comm(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567891)  # Unique identifier
        default_global = {"active_conversations": {}, "pending_requests": {}}
        self.config.register_global(**default_global)
        self.cleanup_pending_requests.start()

    def cog_unload(self):
        self.cleanup_pending_requests.cancel()

    @commands.group()
    async def pm(self, ctx):
        """Group command for managing private communications."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @pm.command(name="start")
    async def start(self, ctx, user: discord.User):
        """Start a private communication with another user."""
        if user == ctx.author:
            await ctx.send("You cannot start a private communication with yourself.")
            return

        async with self.config.pending_requests() as pending_requests:
            if user.id in pending_requests:
                await ctx.send("This user already has a pending request.")
                return

            pending_requests[user.id] = ctx.author.id

        await ctx.send(f"Private communication request sent to {user.name}.")
        await user.send(f"{ctx.author.name} has requested to open communications with you. Do you accept? (yes/no)")

    @pm.command(name="stop")
    async def stop(self, ctx):
        """Stop the private communication."""
        async with self.config.active_conversations() as active_conversations:
            if ctx.author.id in active_conversations:
                other_user_id = active_conversations[ctx.author.id]
                other_user = self.bot.get_user(other_user_id)
                del active_conversations[ctx.author.id]
                del active_conversations[other_user_id]
                await ctx.send("Private communication stopped.")
                await other_user.send(f"{ctx.author.name} has stopped the private communication.")
            else:
                await ctx.send("You have no active private communications.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return  # Ignore bot messages

        if isinstance(message.channel, discord.DMChannel):
            async with self.config.pending_requests() as pending_requests:
                if message.author.id in pending_requests:
                    requester_id = pending_requests[message.author.id]
                    if message.content.lower() == "yes":
                        async with self.config.active_conversations() as active_conversations:
                            active_conversations[message.author.id] = requester_id
                            active_conversations[requester_id] = message.author.id
                        requester = self.bot.get_user(requester_id)
                        await message.author.send(f"Private communication started with {requester.name}.")
                        await requester.send(f"{message.author.name} has accepted your private communication request.")
                        del pending_requests[message.author.id]
                    elif message.content.lower() == "no":
                        requester = self.bot.get_user(requester_id)
                        await message.author.send("Private communication request denied.")
                        await requester.send(f"{message.author.name} has denied your private communication request.")
                        del pending_requests[message.author.id]
                    return

            async with self.config.active_conversations() as active_conversations:
                if message.author.id in active_conversations:
                    other_user_id = active_conversations[message.author.id]
                    other_user = self.bot.get_user(other_user_id)
                    if other_user:
                        await other_user.send(f"**Private message from {message.author.name}**: {message.content}")

    @tasks.loop(minutes=10)
    async def cleanup_pending_requests(self):
        async with self.config.pending_requests() as pending_requests:
            to_remove = []
            for user_id, requester_id in pending_requests.items():
                user = self.bot.get_user(user_id)
                requester = self.bot.get_user(requester_id)
                if user and requester:
                    try:
                        await user.send("Your private communication request has expired.")
                        await requester.send("Your private communication request has expired.")
                    except discord.Forbidden:
                        pass
                to_remove.append(user_id)
            for user_id in to_remove:
                del pending_requests[user_id]

def setup(bot):
    bot.add_cog(Comm(bot))
