import discord
import os
from redbot.core import commands, Config

class Comm(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier="usercomm", force_registration=True)
        self.config.register_global(
            linked_users=[],
            active_sessions={}
        )  # Initialize the configuration
        self.message_references = {}  # Store message references
        self.relayed_messages = {}  # Store relayed messages

    async def send_status_message(self, message, user, title):
        linked_users = await self.config.linked_users()
        embed = discord.Embed(title=title, description=message)
        for user_id in linked_users:
            relay_user = self.bot.get_user(user_id)
            if relay_user and relay_user != user:
                await relay_user.send(embed=embed)

    @commands.group(aliases=['uc'])
    async def usercomm(self, ctx):
        """Manage usercomm connections."""
        pass

    @usercomm.command(name="create")
    async def usercomm_create(self, ctx, name: str, password: str = None):
        """Create a usercomm network with a name and optional password."""
        active_sessions = await self.config.active_sessions()
        if name in active_sessions:
            await ctx.send("A session with this name already exists.")
            return
        active_sessions[name] = {"password": password, "users": []}
        await self.config.active_sessions.set(active_sessions)
        await ctx.send(f"Usercomm network '{name}' created successfully.")

    @usercomm.command(name="join")
    async def usercomm_join(self, ctx, name: str, password: str = None):
        """Join an existing usercomm network with a name and optional password."""
        active_sessions = await self.config.active_sessions()
        if name not in active_sessions:
            await ctx.send("No session found with this name.")
            return
        if active_sessions[name]["password"] and active_sessions[name]["password"] != password:
            await ctx.send("Incorrect password.")
            return

        # Leave any existing usercomm
        for session_name, session_info in active_sessions.items():
            if ctx.author.id in session_info["users"]:
                session_info["users"].remove(ctx.author.id)
                await ctx.send(f"You have left the usercomm network '{session_name}'.")

        if ctx.author.id in active_sessions[name]["users"]:
            await ctx.send("You are already part of this session.")
            return
        active_sessions[name]["users"].append(ctx.author.id)
        await self.config.active_sessions.set(active_sessions)
        await ctx.send(f"You have joined the usercomm network '{name}'.")

    @usercomm.command(name="leave")
    async def usercomm_leave(self, ctx, name: str):
        """Leave an existing usercomm network with a name."""
        active_sessions = await self.config.active_sessions()
        if name not in active_sessions:
            await ctx.send("No session found with this name.")
            return
        if ctx.author.id not in active_sessions[name]["users"]:
            await ctx.send("You are not part of this session.")
            return
        active_sessions[name]["users"].remove(ctx.author.id)
        await self.config.active_sessions.set(active_sessions)
        await ctx.send(f"You have left the usercomm network '{name}'.")

    @usercomm.command(name="changename")
    async def usercomm_changename(self, ctx, new_name: str):
        """Change your display name in the usercomm network."""
        # This command assumes that the user is already part of a usercomm network
        active_sessions = await self.config.active_sessions()
        for session_name, session_info in active_sessions.items():
            if ctx.author.id in session_info["users"]:
                session_info["users"].remove(ctx.author.id)
                session_info["users"].append({"id": ctx.author.id, "name": new_name})
                await self.config.active_sessions.set(active_sessions)
                await ctx.send(f"Your display name has been changed to '{new_name}' in the usercomm network '{session_name}'.")
                return
        await ctx.send("You are not part of any usercomm network.")

    @commands.group()
    async def dmcomm(self, ctx, user_id: int):
        """Open a direct communication with a specific user."""
        user = self.bot.get_user(user_id)
        if not user:
            await ctx.send("User not found.")
            return

        active_sessions = await self.config.active_sessions()
        session_key = f"{ctx.author.id}-{user_id}"

        if session_key in active_sessions:
            await ctx.send("You already have an active session with this user.")
            return

        active_sessions[session_key] = {"users": [ctx.author.id, user_id]}
        await self.config.active_sessions.set(active_sessions)
        await ctx.send(f"Communication line opened with {user.mention}.")
        await user.send(f"{ctx.author.mention} has opened a communication line with you.")

    @dmcomm.command(name="close")
    async def dmcomm_close(self, ctx, user_id: int):
        """Close the direct communication with a specific user."""
        user = self.bot.get_user(user_id)
        if not user:
            await ctx.send("User not found.")
            return

        active_sessions = await self.config.active_sessions()
        session_key = f"{ctx.author.id}-{user_id}"

        if session_key not in active_sessions:
            await ctx.send("You do not have an active session with this user.")
            return

        del active_sessions[session_key]
        await self.config.active_sessions.set(active_sessions)
        await ctx.send(f"Communication line closed with {user.mention}.")
        await user.send(f"{ctx.author.mention} has closed the communication line with you.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        linked_users = await self.config.linked_users()
        active_sessions = await self.config.active_sessions()

        if message.guild:
            # Handle server messages for direct communication
            for session_key, session_info in active_sessions.items():
                if '-' in session_key:
                    user1_id, user2_id = map(int, session_key.split('-'))
                    if message.author.id in (user1_id, user2_id):
                        other_user_id = user1_id if message.author.id == user2_id else user2_id
                        other_user = self.bot.get_user(other_user_id)
                        if other_user:
                            await other_user.send(f"**{message.author.display_name}:** {message.content}")
            return

        if message.author.id in linked_users:
            display_name = message.author.display_name if message.author.display_name else message.author.name

            # Relay the message to other linked users
            content = message.content

            # Handle emojis
            if message.guild:
                content = self.replace_emojis_with_urls(message.guild, content)

            for user_id in linked_users:
                if user_id != message.author.id:
                    user = self.bot.get_user(user_id)
                    if user:
                        if message.attachments:
                            for attachment in message.attachments:
                                relay_message = await user.send(f"**{display_name}:** {content}")
                                await attachment.save(f"temp_{attachment.filename}")
                                with open(f"temp_{attachment.filename}", "rb") as file:
                                    await user.send(file=discord.File(file))
                                os.remove(f"temp_{attachment.filename}")
                        else:
                            relay_message = await user.send(f"**{display_name}:** {content}")
                        self.relayed_messages[(message.id, user_id)] = relay_message.id

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if after.author.bot:
            return

        linked_users = await self.config.linked_users()

        if after.author.id in linked_users:
            display_name = after.author.display_name if after.author.display_name else after.author.name
            content = after.content

            # Handle emojis
            if after.guild:
                content = self.replace_emojis_with_urls(after.guild, content)

            for user_id in linked_users:
                if user_id != after.author.id:
                    user = self.bot.get_user(user_id)
                    if user:
                        if (before.id, user_id) in self.relayed_messages:
                            relay_message_id = self.relayed_messages[(before.id, user_id)]
                            relay_message = await user.fetch_message(relay_message_id)
                            await relay_message.delete()
                            new_relay_message = await user.send(f"**{display_name} (edited):** {content}")
                            self.relayed_messages[(after.id, user_id)] = new_relay_message.id

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:
            return

        linked_users = await self.config.linked_users()

        # Check if the message is in a usercomm channel
        if message.author.id in linked_users:
            for user_id in linked_users:
                if user_id != message.author.id:
                    user = self.bot.get_user(user_id)
                    if user and (message.id, user_id) in self.relayed_messages:
                        relay_message_id = self.relayed_messages[(message.id, user_id)]
                        relay_message = await user.fetch_message(relay_message_id)
                        await relay_message.delete()

    def replace_emojis_with_urls(self, guild, content):
        if guild:
            for emoji in guild.emojis:
                if str(emoji) in content:
                    content = content.replace(str(emoji), str(emoji.url))
        return content

def setup(bot):
    bot.add_cog(Comm(bot))
