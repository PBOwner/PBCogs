import discord
import os
from redbot.core import commands, Config

class Comm(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier="comm", force_registration=True)
        self.config.register_global(
            linked_users=[],
            global_blacklist=[],
            word_filters=[]
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

    @commands.group(aliases=['comm'])
    async def comm(self, ctx):
        """Manage comm connections."""
        pass

    @comm.command(name="open")
    async def comm_open(self, ctx):
        """Link the current user to the comm network."""
        linked_users = await self.config.linked_users()
        if ctx.author.id not in linked_users:
            linked_users.append(ctx.author.id)
            await self.config.linked_users.set(linked_users)
            await ctx.send("You have joined the comm network.")
            await self.send_status_message(f"{ctx.author.mention} has joined the comm.", ctx.author, "User Joined")
        else:
            await ctx.send("You are already part of the comm.")

    @comm.command(name="close")
    async def comm_close(self, ctx):
        """Unlink the current user from the comm network."""
        linked_users = await self.config.linked_users()
        if ctx.author.id in linked_users:
            linked_users.remove(ctx.author.id)
            await self.config.linked_users.set(linked_users)
            await ctx.send("You have left the comm network.")
            await self.send_status_message(f"{ctx.author.mention} has left the comm.", ctx.author, "User Left")
        else:
            await ctx.send("You are not part of the comm.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild:  # Only allow in DMs
            return
        if message.author.bot:
            return

        linked_users = await self.config.linked_users()

        if message.author.id in linked_users:
            global_blacklist = await self.config.global_blacklist()
            word_filters = await self.config.word_filters()

            if message.author.id in global_blacklist:
                return  # Author is globally blacklisted

            if any(word in message.content for word in word_filters):
                await message.author.send("That word is not allowed.")
                await message.delete()  # Message contains a filtered word, notify user and delete it
                return

            display_name = message.author.display_name if message.author.display_name else message.author.name

            # Relay the message to other linked users, removing mentions
            content = message.content

            # Remove @everyone and @here mentions
            content = content.replace("@everyone", "").replace("@here", "")

            # Handle mentions
            mentioned_users = message.mentions
            if mentioned_users:
                for user in mentioned_users:
                    content = content.replace(f"<@{user.id}>", '')  # Remove the mention
                    await user.send(f"You were mentioned by {message.author.mention} in a DM.")

            # If there's no content left after removing mentions
            if not content.strip():
                content = "User Mentioned Blocked"

            # Handle emojis
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
        if after.guild:
            return

        linked_users = await self.config.linked_users()

        if after.author.id in linked_users:
            display_name = after.author.display_name if after.author.display_name else after.author.name
            content = after.content

            # Remove @everyone and @here mentions
            content = content.replace("@everyone", "").replace("@here", "")

            # Handle mentions
            mentioned_users = after.mentions
            if mentioned_users:
                for user in mentioned_users:
                    content = content.replace(f"<@{user.id}>", '')  # Remove the mention
                    await user.send(f"You were mentioned by {after.author.mention} in a DM.")

            # If there's no content left after removing mentions
            if not content.strip():
                content = "User Mentioned Blocked"

            # Handle emojis
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
        if message.guild:
            return

        linked_users = await self.config.linked_users()

        # Check if the message is in a comm channel
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

    @comm.command(name="globalblacklist")
    async def comm_globalblacklist(self, ctx, user: discord.User):
        """Prevent specific members from sending messages through the comm globally."""
        if await self.bot.is_owner(ctx.author):
            global_blacklist = await self.config.global_blacklist()
            if user.id not in global_blacklist:
                global_blacklist.append(user.id)
                await self.config.global_blacklist.set(global_blacklist)
                await ctx.send(f"{user.display_name} has been added to the global comm blacklist.")
            else:
                await ctx.send(f"{user.display_name} is already in the global comm blacklist.")
        else:
            await ctx.send("You must be the bot owner to use this command.")

    @comm.command(name="unglobalblacklist")
    async def comm_unglobalblacklist(self, ctx, user: discord.User):
        """Command to remove a user from the global comm blacklist (Bot Owner Only)."""
        if await self.bot.is_owner(ctx.author):
            global_blacklist = await self.config.global_blacklist()
            if user.id in global_blacklist:
                global_blacklist.remove(user.id)
                await self.config.global_blacklist.set(global_blacklist)
                await ctx.send(f"{user.display_name} has been removed from the global comm blacklist.")
            else:
                await ctx.send(f"{user.display_name} is not in the global comm blacklist.")
        else:
            await ctx.send("You must be the bot owner to use this command.")

    @comm.command(name="addwordfilter")
    async def comm_addwordfilter(self, ctx, *, word: str):
        """Add a word to the comm word filter."""
        if await self.bot.is_owner(ctx.author):
            word_filters = await self.config.word_filters()
            if word not in word_filters:
                word_filters.append(word)
                await self.config.word_filters.set(word_filters)
                await ctx.send(f"`{word}` has been added to the comm word filter.")
            else:
                await ctx.send(f"`{word}` is already in the comm word filter.")

    @comm.command(name="removewordfilter")
    async def comm_removewordfilter(self, ctx, *, word: str):
        """Remove a word from the comm word filter."""
        if await self.bot.is_owner(ctx.author):
            word_filters = await self.config.word_filters()
            if word in word_filters:
                word_filters.remove(word)
                await self.config.word_filters.set(word_filters)
                await ctx.send(f"`{word}` has been removed from the comm word filter.")
            else:
                await ctx.send(f"`{word}` is not in the comm word filter.")

def setup(bot):
    bot.add_cog(Comm(bot))
