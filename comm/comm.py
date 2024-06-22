import discord
import os
from redbot.core import commands, Config
import asyncio
from datetime import datetime, timedelta

class Comm(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier="usercomm", force_registration=True)
        self.config.register_global(
            linked_users=[],
            active_sessions={},
            previous_sessions={},
            user_names={},
            merged_sessions={},
            trusted_users=[],
            banned_users={}
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
        if ctx.guild is not None:
            await ctx.send("This command can only be used in DMs.")
            return False
        return True

    @usercomm.command(name="create")
    async def usercomm_create(self, ctx, name: str, password: str = None):
        """Create a usercomm network with a name and optional password."""
        if not await self.usercomm(ctx):
            return
        active_sessions = await self.config.active_sessions()
        if name in active_sessions:
            await ctx.send("A session with this name already exists.")
            return
        active_sessions[name] = {"password": password, "users": []}
        await self.config.active_sessions.set(active_sessions)
        embed = discord.Embed(title="Usercomm Network Created", description=f"Usercomm network '{name}' created successfully.")
        await ctx.send(embed=embed)

    @usercomm.command(name="join")
    async def usercomm_join(self, ctx, name: str, password: str = None):
        """Join an existing usercomm network with a name and optional password."""
        if not await self.usercomm(ctx):
            return
        active_sessions = await self.config.active_sessions()
        banned_users = await self.config.banned_users()

        if name not in active_sessions:
            await ctx.send("No session found with this name.")
            return
        if active_sessions[name]["password"] and active_sessions[name]["password"] != password:
            await ctx.send("Incorrect password.")
            return

        if ctx.author.id in banned_users and banned_users[ctx.author.id] > asyncio.get_event_loop().time():
            ban_end = datetime.fromtimestamp(banned_users[ctx.author.id])
            ban_end_link = f"https://hammertime.cyou/#{int(ban_end.timestamp())}"
            await ctx.send(f"You are banned from joining usercomm networks until {ban_end_link}.")
            return

        current_sessions = [session_name for session_name, session_info in active_sessions.items() if ctx.author.id in session_info["users"]]

        if current_sessions:
            current_session_name = current_sessions[0]
            await ctx.send(f"You are currently in the usercomm network '{current_session_name}'. Do you want to leave it and join '{name}'? (Yes/No)")

            def check(m):
                return m.author.id == ctx.author.id and m.channel == ctx.channel and m.content.lower() in ["yes", "no"]

            try:
                response = await self.bot.wait_for('message', check=check, timeout=60.0)
                if response.content.lower() == "yes":
                    active_sessions[current_session_name]["users"].remove(ctx.author.id)
                    await ctx.send(f"You have left the usercomm network '{current_session_name}' and joined '{name}'.")
                else:
                    await ctx.send(f"You have decided to stay in the usercomm network '{current_session_name}'.")
                    return
            except asyncio.TimeoutError:
                await ctx.send("You did not respond in time. Please try again.")
                return

        if ctx.author.id in active_sessions[name]["users"]:
            await ctx.send("You are already part of this session.")
            return
        active_sessions[name]["users"].append(ctx.author.id)
        await self.config.active_sessions.set(active_sessions)
        embed = discord.Embed(title="Usercomm Network Joined", description=f"You have joined the usercomm network '{name}'.")
        await ctx.send(embed=embed)

    @usercomm.command(name="leave")
    async def usercomm_leave(self, ctx, name: str):
        """Leave an existing usercomm network with a name."""
        if not await self.usercomm(ctx):
            return
        active_sessions = await self.config.active_sessions()

        if name not in active_sessions:
            await ctx.send("No session found with this name.")
            return
        if ctx.author.id not in active_sessions[name]["users"]:
            await ctx.send("You are not part of this session.")
            return
        active_sessions[name]["users"].remove(ctx.author.id)

        await self.config.active_sessions.set(active_sessions)
        embed = discord.Embed(title="Usercomm Network Left", description=f"You have left the usercomm network '{name}'.")
        await ctx.send(embed=embed)

    @usercomm.command(name="changename")
    async def usercomm_changename(self, ctx, new_name: str):
        """Change your display name in the usercomm network."""
        if not await self.usercomm(ctx):
            return
        user_names = await self.config.user_names()
        user_names[ctx.author.id] = new_name
        await self.config.user_names.set(user_names)
        embed = discord.Embed(title="Display Name Changed", description=f"Your display name has been changed to '{new_name}'.")
        await ctx.send(embed=embed)

    @usercomm.command(name="remove")
    @commands.is_owner()
    async def usercomm_remove(self, ctx, user: discord.User, reason: str, duration: str = "5m"):
        """Remove a user from the usercomm and ban them for a specified duration."""
        if not await self.usercomm(ctx):
            return
        active_sessions = await self.config.active_sessions()
        banned_users = await self.config.banned_users()

        for session_name, session_info in active_sessions.items():
            if user.id in session_info["users"]:
                session_info["users"].remove(user.id)
                embed = discord.Embed(title="User Removed", description=f"{user.display_name} has been removed from the usercomm network '{session_name}' for '{reason}'.")
                await ctx.send(embed=embed)

        ban_duration = self.parse_duration(duration)
        ban_end = datetime.now() + timedelta(seconds=ban_duration)
        banned_users[user.id] = ban_end.timestamp()
        await self.config.active_sessions.set(active_sessions)
        await self.config.banned_users.set(banned_users)
        ban_end_link = f"https://hammertime.cyou/#{int(ban_end.timestamp())}"
        embed = discord.Embed(title="User Banned", description=f"{user.display_name} has been banned for '{reason}' until {ban_end_link}.")
        await ctx.send(embed=embed)
        await user.send(embed=embed)

    @usercomm.command(name="unban")
    @commands.is_owner()
    async def usercomm_unban(self, ctx, user: discord.User):
        """Unban a user from the usercomm."""
        if not await self.usercomm(ctx):
            return
        banned_users = await self.config.banned_users()

        if user.id not in banned_users:
            await ctx.send(f"{user.display_name} is not banned.")
            return

        del banned_users[user.id]
        await self.config.banned_users.set(banned_users)
        embed = discord.Embed(title="User Unbanned", description=f"{user.display_name} has been unbanned from the usercomm network.")
        await ctx.send(embed=embed)
        await user.send(embed=embed)

    @usercomm.command(name="addtrusted")
    @commands.is_owner()
    async def usercomm_addtrusted(self, ctx, user: discord.User):
        """Add a trusted user who can remove other users from the usercomm."""
        if not await self.usercomm(ctx):
            return
        trusted_users = await self.config.trusted_users()
        if user.id not in trusted_users:
            trusted_users.append(user.id)
            await self.config.trusted_users.set(trusted_users)
            embed = discord.Embed(title="Trusted User Added", description=f"{user.display_name} has been added as a trusted user.")
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"{user.display_name} is already a trusted user.")

    @usercomm.command(name="removetrusted")
    @commands.is_owner()
    async def usercomm_removetrusted(self, ctx, user: discord.User):
        """Remove a trusted user."""
        if not await self.usercomm(ctx):
            return
        trusted_users = await self.config.trusted_users()
        if user.id in trusted_users:
            trusted_users.remove(user.id)
            await self.config.trusted_users.set(trusted_users)
            embed = discord.Embed(title="Trusted User Removed", description=f"{user.display_name} has been removed as a trusted user.")
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"{user.display_name} is not a trusted user.")

    @usercomm.command(name="add")
    @commands.is_owner()
    async def usercomm_add(self, ctx, user: discord.User, name: str):
        """Manually add a user back to a usercomm network."""
        if not await self.usercomm(ctx):
            return
        active_sessions = await self.config.active_sessions()

        if name not in active_sessions:
            await ctx.send("No session found with this name.")
            return
        if user.id in active_sessions[name]["users"]:
            await ctx.send(f"{user.display_name} is already part of this session.")
            return
        active_sessions[name]["users"].append(user.id)
        await self.config.active_sessions.set(active_sessions)
        embed = discord.Embed(title="User Added", description=f"{user.display_name} has been added to the usercomm network '{name}'.")
        await ctx.send(embed=embed)

    @usercomm.command(name="listusers")
    @commands.is_owner()
    async def usercomm_listusers(self, ctx, name: str):
        """List all users and their IDs currently connected to a specific usercomm network."""
        if not await self.usercomm(ctx):
            return
        active_sessions = await self.config.active_sessions()
        user_names = await self.config.user_names()

        if name not in active_sessions:
            await ctx.send("No session found with this name.")
            return

        users_list = "\n".join([f"{user_id}: {user_names.get(user_id, 'Unknown')}" for user_id in active_sessions[name]["users"]])
        if not users_list:
            users_list = "No users found."
        await ctx.send(f"```\nUsers in '{name}' and their IDs:\n{users_list}\n```")

    @usercomm.command(name="listcomms")
    @commands.is_owner()
    async def usercomm_listcomms(self, ctx):
        """List all existing usercomm networks."""
        if not await self.usercomm(ctx):
            return
        active_sessions = await self.config.active_sessions()
        comms_list = "\n".join(active_sessions.keys())
        if not comms_list:
            comms_list = "No usercomm networks found."
        await ctx.send(f"```\nExisting usercomm networks:\n{comms_list}\n```")

    @commands.group()
    async def dmcomm(self, ctx):
        """Manage direct communications with specific users."""
        if ctx.guild is None:
            await ctx.send("This command can only be used in servers.")
            return False
        return True

    @dmcomm.command(name="open")
    async def dmcomm_open(self, ctx, user_id: int):
        """Open a direct communication with a specific user."""
        if not await self.dmcomm(ctx):
            return
        user = self.bot.get_user(user_id)
        if not user:
            await ctx.send("User not found.")
            return

        active_sessions = await self.config.active_sessions()
        previous_sessions = await self.config.previous_sessions()
        session_key = f"{ctx.author.id}-{user_id}"

        if session_key in active_sessions:
            await ctx.send("You already have an active session with this user.")
            return

        # Ask the target user for confirmation
        def check(m):
            return m.author.id == user_id and m.channel == user.dm_channel and m.content.lower() in ["yes", "no"]

        await user.send(f"{ctx.author.mention} wants to open a communication line with you. Do you accept this transmission? Yes or No?")

        try:
            response = await self.bot.wait_for('message', check=check, timeout=60.0)
            if response.content.lower() == "yes":
                # Save and close all existing usercomms for the target user
                previous_sessions[user_id] = []
                for session_name, session_info in active_sessions.items():
                    if user_id in session_info["users"]:
                        session_info["users"].remove(user_id)
                        previous_sessions[user_id].append(session_name)
                        await user.send(f"You have been removed from the usercomm network '{session_name}'.")

                active_sessions[session_key] = {"users": [ctx.author.id, user_id]}
                await self.config.active_sessions.set(active_sessions)
                await self.config.previous_sessions.set(previous_sessions)
                await ctx.send(f"Communication line opened with {user.mention}.")
                await user.send(f"{ctx.author.mention} has opened a communication line with you.")
            else:
                await ctx.send(f"{user.mention} has denied the communication request.")
        except asyncio.TimeoutError:
            await ctx.send(f"{user.mention} did not respond to the communication request in time.")

    @dmcomm.command(name="close")
    async def dmcomm_close(self, ctx):
        """Close the direct communication with a specific user."""
        if not await self.dmcomm(ctx):
            return
        active_sessions = await self.config.active_sessions()
        previous_sessions = await self.config.previous_sessions()
        session_keys_to_remove = []

        for session_key, session_info in active_sessions.items():
            if ctx.author.id in session_info["users"]:
                session_keys_to_remove.append(session_key)
                other_user_id = session_info["users"][1] if session_info["users"][0] == ctx.author.id else session_info["users"][0]
                other_user = self.bot.get_user(other_user_id)
                if other_user:
                    await other_user.send(f"{ctx.author.mention} has closed the communication line with you.")

                # Reestablish previous usercomms for the other user
                if other_user_id in previous_sessions:
                    for session_name in previous_sessions[other_user_id]:
                        active_sessions[session_name]["users"].append(other_user_id)
                        await other_user.send(f"You have been re-added to the usercomm network '{session_name}'.")
                    del previous_sessions[other_user_id]

        for session_key in session_keys_to_remove:
            del active_sessions[session_key]

        await self.config.active_sessions.set(active_sessions)
        await self.config.previous_sessions.set(previous_sessions)
        await ctx.send("All direct communication lines have been closed.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        active_sessions = await self.config.active_sessions()
        user_names = await self.config.user_names()
        trusted_users = await self.config.trusted_users()

        if message.guild:
            # Handle server messages for direct communication
            for session_name, session_info in active_sessions.items():
                if message.author.id in session_info["users"]:
                    display_name = user_names.get(message.author.id, message.author.display_name)
                    if message.author.id in trusted_users:
                        display_name += " - Moderator"
                    for user_id in session_info["users"]:
                        if user_id != message.author.id:
                            user = self.bot.get_user(user_id)
                            if user:
                                if message.attachments:
                                    for attachment in message.attachments:
                                        await user.send(f"**{message.guild.name} - {display_name}:** {message.content}")
                                        await attachment.save(f"temp_{attachment.filename}")
                                        with open(f"temp_{attachment.filename}", "rb") as file:
                                            await user.send(file=discord.File(file))
                                        os.remove(f"temp_{attachment.filename}")
                                else:
                                    await user.send(f"**{message.guild.name} - {display_name}:** {message.content}")
            return

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if after.author.bot:
            return

        active_sessions = await self.config.active_sessions()
        user_names = await self.config.user_names()
        trusted_users = await self.config.trusted_users()

        if after.author.id in active_sessions:
            display_name = user_names.get(after.author.id, after.author.display_name)
            if after.author.id in trusted_users:
                display_name += " - Moderator"
            content = after.content

            sessions_to_relay = [session_name for session_name, session_info in active_sessions.items() if after.author.id in session_info["users"]]

            for session_name in sessions_to_relay:
                for user_id in active_sessions[session_name]["users"]:
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

        active_sessions = await self.config.active_sessions()

        # Check if the message is in a usercomm channel
        for session_name, session_info in active_sessions.items():
            if message.channel.id in session_info["users"]:
                for user_id in session_info["users"]:
                    if user_id != message.author.id:
                        user = self.bot.get_user(user_id)
                        if user:
                            async for msg in user.history(limit=100):
                                if msg.content == f"**{message.guild.name} - {message.author.display_name}:** {message.content}":
                                    await msg.delete()
                                    break

def setup(bot):
    bot.add_cog(Comm(bot))
