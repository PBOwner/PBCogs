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
                await relay_user.send(f"***The comms are shifting...** {user.name}: {message}*")

    def get_highest_role(self, member):
        """Get the highest role of a member, excluding @everyone."""
        roles = [role for role in member.roles if role.name != "@everyone"]
        if roles:
            return max(roles, key=lambda role: role.position).name
        return "No Role"

    @commands.group(aliases=['pc'])
    async def privatecomm(self, ctx):
        """Manage private comm connections."""
        pass

    @privatecomm.command(name="create")
    async def privatecomm_create(self, ctx, user: discord.User):
        """Create a private comm from DM to the channel it originated from."""
        private_comms = await self.config.private_comms()
        if ctx.channel.id not in private_comms:
            private_comms[ctx.channel.id] = {"channel_id": ctx.channel.id, "users": [ctx.author.id, user.id]}
            await self.config.private_comms.set(private_comms)
            await ctx.send(f"Private comm created between {ctx.author.display_name} and {user.display_name}.")
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
        if not isinstance(message.channel, discord.DMChannel):
            return
        if message.author.bot:
            return

        # Check if the message is a bot command
        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return  # Ignore bot commands

        private_comms = await self.config.private_comms()

        # Check if the message is in a private comm
        for comm_id, comm_data in private_comms.items():
            users = comm_data["users"]
            if message.author.id in users:
                display_name = message.author.display_name if message.author.display_name else message.author.name
                highest_role = self.get_highest_role(message.author)

                for user_id in users:
                    if user_id != message.author.id:
                        user = self.bot.get_user(user_id)
                        if user:
                            if message.attachments:
                                for attachment in message.attachments:
                                    await user.send(f"**{highest_role} - {display_name}:** {message.content}")
                                    await attachment.save(f"temp_{attachment.filename}")
                                    with open(f"temp_{attachment.filename}", "rb") as file:
                                        await user.send(file=discord.File(file))
                                    os.remove(f"temp_{attachment.filename}")
                            else:
                                await user.send(f"**{highest_role} - {display_name}:** {message.content}")

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if not isinstance(message.channel, discord.DMChannel):
            return

        private_comms = await self.config.private_comms()

        # Check if the message is in a private comm
        for comm_id, comm_data in private_comms.items():
            users = comm_data["users"]
            if message.author.id in users:
                for user_id in users:
                    if user_id != message.author.id:
                        user = self.bot.get_user(user_id)
                        if user:
                            async for msg in user.history(limit=100):
                                highest_role = self.get_highest_role(message.author)
                                if msg.content == f"**{highest_role} - {message.author.display_name}:** {message.content}":
                                    await msg.delete()
                                    break

def setup(bot):
    bot.add_cog(PrivateComm(bot))
