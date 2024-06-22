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
    async def privatecomm_create(self, ctx, name: str, password: str):
        """Create a private comm with a name and password."""
        private_comms = await self.config.private_comms()
        if name not in private_comms:
            private_comms[name] = {"password": password, "users": [ctx.author.id]}
            await self.config.private_comms.set(private_comms)
            await ctx.send(f"Private comm `{name}` created with the provided password.")
        else:
            await ctx.send("A private comm with this name already exists.")

    @privatecomm.command(name="join")
    async def privatecomm_join(self, ctx, name: str, password: str):
        """Join an existing private comm with the correct name and password."""
        private_comms = await self.config.private_comms()
        if name in private_comms:
            if private_comms[name]["password"] == password:
                if ctx.author.id not in private_comms[name]["users"]:
                    private_comms[name]["users"].append(ctx.author.id)
                    await self.config.private_comms.set(private_comms)
                    await ctx.send(f"You have joined the private comm `{name}`.")
                    await self.send_status_message(f"A faint signal was picked up from {ctx.author.name}, connection has been established.", ctx.author, name)
                else:
                    await ctx.send("You are already part of the private comm.")
            else:
                await ctx.send("Incorrect password for the private comm.")
        else:
            await ctx.send("No private comm found with this name.")

    @privatecomm.command(name="leave")
    async def privatecomm_leave(self, ctx, name: str):
        """Leave a private comm."""
        private_comms = await self.config.private_comms()
        if name in private_comms and ctx.author.id in private_comms[name]["users"]:
            private_comms[name]["users"].remove(ctx.author.id)
            if not private_comms[name]["users"]:
                del private_comms[name]
            await self.config.private_comms.set(private_comms)
            await ctx.send(f"You have left the private comm `{name}`.")
        else:
            await ctx.send("You are not part of the private comm with this name.")

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
        for name, comm_data in private_comms.items():
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
        for name, comm_data in private_comms.items():
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
