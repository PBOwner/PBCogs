import discord
import os
from redbot.core import commands, Config

class Comm(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier="comm", force_registration=True)
        self.config.register_global(
            linked_channels_list=[],
            user_display_names={}
        )  # Initialize the configuration
        self.message_references = {}  # Store message references
        self.relayed_messages = {}  # Store relayed messages

    async def send_status_message(self, message, channel, title):
        linked_channels = await self.config.linked_channels_list()
        embed = discord.Embed(title=title, description=f"{message}")
        for channel_id in linked_channels:
            relay_channel = self.bot.get_channel(channel_id)
            if relay_channel and relay_channel != channel:
                await relay_channel.send(embed=embed)

    @commands.group(aliases=['uc'])
    async def usercomm(self, ctx):
        """Manage usercomm connections."""
        if not isinstance(ctx.channel, discord.DMChannel):
            return await ctx.send("This command can only be used in DMs.")
        pass

    @usercomm.command(name="open")
    async def usercomm_open(self, ctx):
        """Link the current DM to the Communications channel."""
        if not isinstance(ctx.channel, discord.DMChannel):
            return await ctx.send("This command can only be used in DMs.")
        linked_channels = await self.config.linked_channels_list()
        if ctx.channel.id not in linked_channels:
            linked_channels.append(ctx.channel.id)
            await self.config.linked_channels_list.set(linked_channels)
            embed = discord.Embed(title="Success!", description="You have joined the Communications channel.")
            await ctx.send(embed=embed)
            await self.send_status_message(f"{ctx.author.name} has joined the Communications channel.", ctx.channel, "Success!")
        else:
            embed = discord.Embed(title="Error", description="You are already part of the Communications channel.")
            await ctx.send(embed=embed)

    @usercomm.command(name="close")
    async def usercomm_close(self, ctx):
        """Unlink the current DM from the Communications channel."""
        if not isinstance(ctx.channel, discord.DMChannel):
            return await ctx.send("This command can only be used in DMs.")
        linked_channels = await self.config.linked_channels_list()
        if ctx.channel.id in linked_channels:
            linked_channels.remove(ctx.channel.id)
            await self.config.linked_channels_list.set(linked_channels)
            embed = discord.Embed(title="Success!", description="You have been severed from the Communications channel.")
            await ctx.send(embed=embed)
            await self.send_status_message(f"The signal from {ctx.author.name} has become too faint to be picked up, the connection was lost.", ctx.channel, "Success!")
        else:
            embed = discord.Embed(title="Error", description="You are not part of the Communications channel.")
            await ctx.send(embed=embed)

    @usercomm.command(name="setname")
    async def usercomm_setname(self, ctx, *, new_name: str):
        """Set a new display name for yourself in the Communications channel."""
        if not isinstance(ctx.channel, discord.DMChannel):
            return await ctx.send("This command can only be used in DMs.")
        user_display_names = await self.config.user_display_names()
        user_display_names[ctx.author.id] = new_name
        await self.config.user_display_names.set(user_display_names)
        await ctx.send(f"Your display name has been changed to {new_name}.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not isinstance(message.channel, discord.DMChannel):
            return

        # Check if the message is a bot command
        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return  # Ignore bot commands

        linked_channels = await self.config.linked_channels_list()
        user_display_names = await self.config.user_display_names()
        display_name = user_display_names.get(message.author.id, message.author.name)

        if message.channel.id in linked_channels:
            # Store the message reference
            self.message_references[message.id] = (message.author.id, None)

            # Relay the message to other linked channels
            content = message.content

            # Handle emojis
            content = self.replace_emojis_with_urls(None, content)

            for channel_id in linked_channels:
                if channel_id != message.channel.id:
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        if message.attachments:
                            for attachment in message.attachments:
                                relay_message = await channel.send(f"**{display_name}:** {content}")
                                await attachment.save(f"temp_{attachment.filename}")
                                with open(f"temp_{attachment.filename}", "rb") as file:
                                    await channel.send(file=discord.File(file))
                                os.remove(f"temp_{attachment.filename}")
                        else:
                            relay_message = await channel.send(f"**{display_name}:** {content}")
                        self.relayed_messages[(message.id, channel_id)] = relay_message.id

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if after.author.bot or not isinstance(after.channel, discord.DMChannel):
            return

        linked_channels = await self.config.linked_channels_list()
        user_display_names = await self.config.user_display_names()
        display_name = user_display_names.get(after.author.id, after.author.name)

        if after.channel.id in linked_channels:
            content = after.content

            # Handle emojis
            content = self.replace_emojis_with_urls(None, content)

            for channel_id in linked_channels:
                if channel_id != after.channel.id:
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        if (before.id, channel_id) in self.relayed_messages:
                            relay_message_id = self.relayed_messages[(before.id, channel_id)]
                            relay_message = await channel.fetch_message(relay_message_id)
                            await relay_message.delete()
                            new_relay_message = await channel.send(f"**{display_name} (edited):** {content}")
                            self.relayed_messages[(after.id, channel_id)] = new_relay_message.id

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot or not isinstance(message.channel, discord.DMChannel):
            return

        linked_channels = await self.config.linked_channels_list()

        # Check if the message is in a Communications channel
        if message.channel.id in linked_channels:
            for channel_id in linked_channels:
                if channel_id != message.channel.id:
                    channel = self.bot.get_channel(channel_id)
                    if channel and (message.id, channel_id) in self.relayed_messages:
                        relay_message_id = self.relayed_messages[(message.id, channel_id)]
                        relay_message = await channel.fetch_message(relay_message_id)
                        await relay_message.delete()

    def replace_emojis_with_urls(self, guild, content):
        if guild:
            for emoji in guild.emojis:
                if str(emoji) in content:
                    content = content.replace(str(emoji), str(emoji.url))
        return content

def setup(bot):
    bot.add_cog(Comm(bot))
