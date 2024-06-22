import discord
import os
from redbot.core import commands, Config

class PrivateComm(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier="private_comm", force_registration=True)
        self.config.register_global(
            private_comms={}
        )  # Initialize the configuration

    async def send_status_message(self, message, user, comm_key):
        comm_data = await self.config.private_comms.get_raw(comm_key, default={})
        linked_users = comm_data.get("users", [])

        for user_id in linked_users:
            relay_user = self.bot.get_user(user_id)
            if relay_user and relay_user != user:
                await relay_user.send(f"***The comms are shifting...** {user.display_name}: {message}*")

    @commands.group(aliases=['pc'])
    async def privatecomm(self, ctx):
        """Manage private comm connections."""
        pass

    @privatecomm.command(name="create")
    async def privatecomm_create(self, ctx, user: discord.User):
        """Create a private comm from a channel to the user's DM."""
        if isinstance(ctx.channel, discord.DMChannel):
            return await ctx.send("This command can only be used in a server channel.")

        private_comms = await self.config.private_comms()
        if ctx.channel.id not in private_comms:
            private_comms[ctx.channel.id] = {"channel_id": ctx.channel.id, "users": [ctx.author.id, user.id], "dm_user_id": user.id}
            await self.config.private_comms.set(private_comms)
            await ctx.send(f"Private comm created between this channel and {user.display_name}'s DM.")
        else:
            await ctx.send("A private comm already exists for this channel.")

    @privatecomm.command(name="join")
    async def privatecomm_join(self, ctx, user: discord.User):
        """Join an existing private comm."""
        private_comms = await self.config.private_comms()
        if ctx.channel.id in private_comms:
            if user.id not in private_comms[ctx.channel.id]["users"]:
                private_comms[ctx.channel.id]["users"].append(user.id)
                await self.config.private_comms.set(private_comms)
                await ctx.send(f"{user.display_name} has joined the private comm.")
                await self.send_status_message(f"{user.display_name} has joined the comm.", user, ctx.channel.id)
            else:
                await ctx.send(f"{user.display_name} is already part of the private comm.")
        else:
            await ctx.send("No private comm found for this channel.")

    @privatecomm.command(name="leave")
    async def privatecomm_leave(self, ctx):
        """Leave a private comm."""
        private_comms = await self.config.private_comms()
        if ctx.channel.id in private_comms and ctx.author.id in private_comms[ctx.channel.id]["users"]:
            private_comms[ctx.channel.id]["users"].remove(ctx.author.id)
            if not private_comms[ctx.channel.id]["users"]:
                del private_comms[ctx.channel.id]
            await self.config.private_comms.set(private_comms)
            await ctx.send(f"{ctx.author.display_name} has left the private comm.")
        else:
            await ctx.send("You are not part of a private comm in this channel.")

    @privatecomm.command(name="delete")
    async def privatecomm_delete(self, ctx):
        """Delete a private comm."""
        private_comms = await self.config.private_comms()
        if ctx.channel.id in private_comms:
            del private_comms[ctx.channel.id]
            await self.config.private_comms.set(private_comms)
            await ctx.send("The private comm has been deleted.")
        else:
            await ctx.send("No private comm found for this channel.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # Check if the message is a bot command
        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return  # Ignore bot commands

        private_comms = await self.config.private_comms()

        # Check if the message is in a private comm
        if isinstance(message.channel, discord.TextChannel):
            if message.channel.id in private_comms:
                comm_data = private_comms[message.channel.id]
                dm_user_id = comm_data["dm_user_id"]
                user = self.bot.get_user(dm_user_id)
                if user:
                    display_name = message.author.display_name
                    if message.attachments:
                        for attachment in message.attachments:
                            await user.send(f"**{display_name}:** {message.content}")
                            await attachment.save(f"temp_{attachment.filename}")
                            with open(f"temp_{attachment.filename}", "rb") as file:
                                await user.send(file=discord.File(file))
                            os.remove(f"temp_{attachment.filename}")
                    else:
                        await user.send(f"**{display_name}:** {message.content}")

        elif isinstance(message.channel, discord.DMChannel):
            for comm_id, comm_data in private_comms.items():
                if message.author.id == comm_data.get("dm_user_id"):
                    channel = self.bot.get_channel(comm_data["channel_id"])
                    if channel:
                        display_name = message.author.display_name
                        if message.attachments:
                            for attachment in message.attachments:
                                await channel.send(f"**{display_name}:** {message.content}")
                                await attachment.save(f"temp_{attachment.filename}")
                                with open(f"temp_{attachment.filename}", "rb") as file:
                                    await channel.send(file=discord.File(file))
                                os.remove(f"temp_{attachment.filename}")
                        else:
                            await channel.send(f"**{display_name}:** {message.content}")

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        private_comms = await self.config.private_comms()

        # Check if the message is in a private comm
        if isinstance(message.channel, discord.TextChannel):
            if message.channel.id in private_comms:
                comm_data = private_comms[message.channel.id]
                dm_user_id = comm_data["dm_user_id"]
                user = self.bot.get_user(dm_user_id)
                if user:
                    async for msg in user.history(limit=100):
                        if msg.content == f"**{message.author.display_name}:** {message.content}":
                            await msg.delete()
                            break

        elif isinstance(message.channel, discord.DMChannel):
            for comm_id, comm_data in private_comms.items():
                if message.author.id == comm_data.get("dm_user_id"):
                    channel = self.bot.get_channel(comm_data["channel_id"])
                    if channel:
                        async for msg in channel.history(limit=100):
                            if msg.content == f"**{message.author.display_name}:** {message.content}":
                                await msg.delete()
                                break

def setup(bot):
    bot.add_cog(PrivateComm(bot))
