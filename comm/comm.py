import discord
import os
from redbot.core import commands, Config

class Comm(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier="comm", force_registration=True)
        self.config.register_global(
            linked_channels_list=[]
        )  # Initialize the configuration
        self.message_references = {}  # Store message references
        self.relayed_messages = {}  # Store relayed messages

    async def send_status_message(self, message, channel, title):
        linked_channels = await self.config.linked_channels_list()
        guild = channel.guild if channel.guild else "DM"
        embed = discord.Embed(title=title, description=f"{guild}: {message}")
        for channel_id in linked_channels:
            relay_channel = self.bot.get_channel(channel_id)
            if relay_channel and relay_channel != channel:
                await relay_channel.send(embed=embed)

    @commands.group(aliases=['comm'])
    async def comm(self, ctx):
        """Manage comm connections."""
        pass

    @comm.command(name="open")
    async def comm_open(self, ctx):
        """Link the current channel to the comm network."""
        linked_channels = await self.config.linked_channels_list()
        if ctx.channel.id not in linked_channels:
            linked_channels.append(ctx.channel.id)
            await self.config.linked_channels_list.set(linked_channels)
            embed = discord.Embed(title="Success!", description="This channel has joined the comm network.")
            await ctx.send(embed=embed)
            await self.send_status_message(f"A signal was picked up from {ctx.channel.mention}, connection has been established.", ctx.channel, "Success!")
        else:
            embed = discord.Embed(title="Error", description="This channel is already part of the comm network.")
            await ctx.send(embed=embed)

    @comm.command(name="close")
    async def comm_close(self, ctx):
        """Unlink the current channel from the comm network."""
        linked_channels = await self.config.linked_channels_list()
        if ctx.channel.id in linked_channels:
            linked_channels.remove(ctx.channel.id)
            await self.config.linked_channels_list.set(linked_channels)
            embed = discord.Embed(title="Success!", description="This channel has been severed from the comm network.")
            await ctx.send(embed=embed)
            await self.send_status_message(f"The signal from {ctx.channel.mention} has become too faint to be picked up, the connection was lost.", ctx.channel, "Success!")
        else:
            embed = discord.Embed(title="Error", description="This channel is not part of the comm network.")
            await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.channel.permissions_for(message.guild.me).send_messages:
            return
        if isinstance(message.channel, discord.TextChannel) and message.content.startswith(commands.when_mentioned(self.bot, message)[0]):
            return  # Ignore bot commands

        # Check if the message is a bot command
        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return  # Ignore bot commands

        linked_channels = await self.config.linked_channels_list()

        if message.channel.id in linked_channels:
            display_name = message.author.name  # Use the author's username instead of display name

            # Store the message reference
            self.message_references[message.id] = (message.author.id, message.guild.id if message.guild else None)

            # Relay the message to other linked channels, removing mentions
            content = message.content

            # Remove @everyone and @here mentions
            content = content.replace("@everyone", "").replace("@here", "")

            # Handle mentions
            mentioned_users = message.mentions
            if mentioned_users:
                for user in mentioned_users:
                    content = content.replace(f"<@{user.id}>", '')  # Remove the mention
                    embed = discord.Embed(title="You were mentioned!")
                    embed.add_field(name="Who", value=message.author.mention, inline=False)
                    embed.add_field(name="Where", value=f"{message.channel.mention} in {message.guild.name if message.guild else 'DM'}", inline=False)
                    embed.add_field(name="When", value=message.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
                    await user.send(embed=embed)

            # If there's no content left after removing mentions
            if not content.strip():
                content = "User Mentioned Blocked"

            # Handle emojis
            content = self.replace_emojis_with_urls(message.guild, content)

            for channel_id in linked_channels:
                if channel_id != message.channel.id:
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        if message.attachments:
                            for attachment in message.attachments:
                                relay_message = await channel.send(f"**{message.guild.name if message.guild else 'DM'} - {display_name}:** {content}")
                                await attachment.save(f"temp_{attachment.filename}")
                                with open(f"temp_{attachment.filename}", "rb") as file:
                                    await channel.send(file=discord.File(file))
                                os.remove(f"temp_{attachment.filename}")
                        else:
                            relay_message = await channel.send(f"**{message.guild.name if message.guild else 'DM'} - {display_name}:** {content}")
                        self.relayed_messages[(message.id, channel_id)] = relay_message.id

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if after.author.bot:
            return

        linked_channels = await self.config.linked_channels_list()

        if after.channel.id in linked_channels:
            display_name = after.author.name  # Use the author's username instead of display name
            content = after.content

            # Remove @everyone and @here mentions
            content = content.replace("@everyone", "").replace("@here", "")

            # Handle mentions
            mentioned_users = after.mentions
            if mentioned_users:
                for user in mentioned_users:
                    content = content.replace(f"<@{user.id}>", '')  # Remove the mention
                    embed = discord.Embed(title="You were mentioned!")
                    embed.add_field(name="Who", value=after.author.mention, inline=False)
                    embed.add_field(name="Where", value=f"{after.channel.mention} in {after.guild.name if after.guild else 'DM'}", inline=False)
                    embed.add_field(name="When", value=after.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
                    await user.send(embed=embed)

            # If there's no content left after removing mentions
            if not content.strip():
                content = "User Mentioned Blocked"

            # Handle emojis
            content = self.replace_emojis_with_urls(after.guild, content)

            for channel_id in linked_channels:
                if channel_id != after.channel.id:
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        if (before.id, channel_id) in self.relayed_messages:
                            relay_message_id = self.relayed_messages[(before.id, channel_id)]
                            relay_message = await channel.fetch_message(relay_message_id)
                            await relay_message.delete()
                            new_relay_message = await channel.send(f"**{after.guild.name if after.guild else 'DM'} - {display_name} (edited):** {content}")
                            self.relayed_messages[(after.id, channel_id)] = new_relay_message.id

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:
            return

        linked_channels = await self.config.linked_channels_list()

        # Check if the message is in a comm channel
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
