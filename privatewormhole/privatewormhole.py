
import discord
import os
from redbot.core import commands, Config

class PrivateWormHole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier="private_wormhole", force_registration=True)
        self.config.register_global(
            private_wormholes={},
            global_blacklist=[],
            word_filters=[]
        )  # Initialize the configuration

    async def send_status_message(self, message, channel, wormhole_key):
        wormhole_data = await self.config.private_wormholes.get_raw(wormhole_key, default={})
        linked_channels = wormhole_data.get("channels", [])

        guild = channel.guild
        for channel_id in linked_channels:
            relay_channel = self.bot.get_channel(channel_id)
            if relay_channel and relay_channel != channel:
                await relay_channel.send(f"***The wormhole is shifting...** {guild.name}: {message}*")

    @commands.group()
    async def privatewormhole(self, ctx):
        """Manage private wormhole connections."""
        pass

    @privatewormhole.command(name="create")
    async def privatewormhole_create(self, ctx, name: str, password: str):
        """Create a private wormhole with a name and password."""
        private_wormholes = await self.config.private_wormholes()
        if name not in private_wormholes:
            private_wormholes[name] = {"password": password, "channels": [ctx.channel.id]}
            await self.config.private_wormholes.set(private_wormholes)
            await ctx.send(f"Private wormhole `{name}` created with the provided password.")
        else:
            await ctx.send("A private wormhole with this name already exists.")

    @privatewormhole.command(name="join")
    async def privatewormhole_join(self, ctx, name: str, password: str):
        """Join an existing private wormhole with the correct name and password."""
        private_wormholes = await self.config.private_wormholes()
        if name in private_wormholes:
            if private_wormholes[name]["password"] == password:
                if ctx.channel.id not in private_wormholes[name]["channels"]:
                    private_wormholes[name]["channels"].append(ctx.channel.id)
                    await self.config.private_wormholes.set(private_wormholes)
                    await ctx.send(f"This channel has joined the private wormhole `{name}`.")
                    await self.send_status_message(f"A faint signal was picked up from {ctx.channel.mention}, connection has been established.", ctx.channel, name)
                else:
                    await ctx.send("This channel is already part of the private wormhole.")
            else:
                await ctx.send("Incorrect password for the private wormhole.")
        else:
            await ctx.send("No private wormhole found with this name.")

    @privatewormhole.command(name="leave")
    async def privatewormhole_leave(self, ctx, name: str):
        """Leave a private wormhole."""
        private_wormholes = await self.config.private_wormholes()
        if name in private_wormholes and ctx.channel.id in private_wormholes[name]["channels"]:
            private_wormholes[name]["channels"].remove(ctx.channel.id)
            if not private_wormholes[name]["channels"]:
                del private_wormholes[name]
            await self.config.private_wormholes.set(private_wormholes)
            await ctx.send(f"This channel has left the private wormhole `{name}`.")
        else:
            await ctx.send("This channel is not part of the private wormhole with this name.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild:  # Don't allow in DMs
            return
        if message.author.bot or not message.channel.permissions_for(message.guild.me).send_messages:
            return
        if isinstance(message.channel, discord.TextChannel) and message.content.startswith(commands.when_mentioned(self.bot, message)[0]):
            return  # Ignore bot commands

        # Check if the message is a bot command
        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return  # Ignore bot commands

        global_blacklist = await self.config.global_blacklist()
        word_filters = await self.config.word_filters()
        private_wormholes = await self.config.private_wormholes()

        if message.author.id in global_blacklist:
            return  # Author is globally blacklisted

        # Check if the message is in a private wormhole channel
        for name, wormhole_data in private_wormholes.items():
            channels = wormhole_data["channels"]
            if message.channel.id in channels:
                if any(word in message.content for word in word_filters):
                    await message.channel.send("That word is not allowed.")
                    await message.delete()
                    return  # Message contains a filtered word, notify user and delete it

                if message.channel.is_nsfw():
                    await message.channel.send("NSFW content is not allowed in the wormhole.")
                    await message.delete()
                    return  # Delete NSFW messages

                display_name = message.author.display_name if message.author.display_name else message.author.name

                for channel_id in channels:
                    if channel_id != message.channel.id:
                        channel = self.bot.get_channel(channel_id)
                        if channel:
                            if message.attachments:
                                for attachment in message.attachments:
                                    await channel.send(f"**{message.guild.name} - {display_name}:** {message.content}")
                                    await attachment.save(f"temp_{attachment.filename}")
                                    with open(f"temp_{attachment.filename}", "rb") as file:
                                        await channel.send(file=discord.File(file))
                                    os.remove(f"temp_{attachment.filename}")
                            else:
                                await channel.send(f"**{message.guild.name} - {display_name}:** {message.content}")

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if not message.guild:
            return

        private_wormholes = await self.config.private_wormholes()

        # Check if the message is in a private wormhole channel
        for name, wormhole_data in private_wormholes.items():
            channels = wormhole_data["channels"]
            if message.channel.id in channels:
                for channel_id in channels:
                    if channel_id != message.channel.id:
                        channel = self.bot.get_channel(channel_id)
                        if channel:
                            async for msg in channel.history(limit=100):
                                if msg.content == f"**{message.guild.name} - {message.author.display_name}:** {message.content}":
                                    await msg.delete()
                                    break

    @privatewormhole.command(name="globalblacklist")
    async def privatewormhole_globalblacklist(self, ctx, user: discord.User):
        """Prevent specific members from sending messages through the private wormhole globally."""
        if await self.bot.is_owner(ctx.author):
            global_blacklist = await self.config.global_blacklist()
            if user.id not in global_blacklist:
                global_blacklist.append(user.id)
                await self.config.global_blacklist.set(global_blacklist)
                await ctx.send(f"{user.display_name} has been added to the global private wormhole blacklist.")
            else:
                await ctx.send(f"{user.display_name} is already in the global private wormhole blacklist.")
        else:
            await ctx.send("You must be the bot owner to use this command.")

    @privatewormhole.command(name="unglobalblacklist")
    async def privatewormhole_unglobalblacklist(self, ctx, user: discord.User):
        """Command to remove a user from the global private wormhole blacklist (Bot Owner Only)."""
        if await self.bot.is_owner(ctx.author):
            global_blacklist = await self.config.global_blacklist()
            if user.id in global_blacklist:
                global_blacklist.remove(user.id)
                await self.config.global_blacklist.set(global_blacklist)
                await ctx.send(f"{user.display_name} has been removed from the global private wormhole blacklist.")
            else:
                await ctx.send(f"{user.display_name} is not in the global private wormhole blacklist.")
        else:
            await ctx.send("You must be the bot owner to use this command.")

    @privatewormhole.command(name="addwordfilter")
    async def privatewormhole_addwordfilter(self, ctx, *, word: str):
        """Add a word to the private wormhole word filter."""
        if await self.bot.is_owner(ctx.author):
            word_filters = await self.config.word_filters()
            if word not in word_filters:
                word_filters.append(word)
                await self.config.word_filters.set(word_filters)
                await ctx.send(f"`{word}` has been added to the private wormhole word filter.")
            else:
                await ctx.send(f"`{word}` is already in the private wormhole word filter.")

    @privatewormhole.command(name="removewordfilter")
    async def privatewormhole_removewordfilter(self, ctx, *, word: str):
        """Remove a word from the private wormhole word filter."""
        if await self.bot.is_owner(ctx.author):
            word_filters = await self.config.word_filters()
            if word in word_filters:
                word_filters.remove(word)
                await self.config.word_filters.set(word_filters)
                await ctx.send(f"`{word}` has been removed from the private wormhole word filter.")
            else:
                await ctx.send(f"`{word}` is not in the private wormhole word filter.")

def setup(bot):
    bot.add_cog(PrivateWormHole(bot))
