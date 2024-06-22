import discord
from redbot.core import commands, Config

class PrivateComm(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier="private_comm", force_registration=True)
        self.config.register_global(
            relays={}
        )  # Initialize the configuration

    @commands.group()
    async def relaydm(self, ctx):
        """Manage DM relays."""
        pass

    @relaydm.command(name="start")
    async def relaydm_start(self, ctx, user: discord.User):
        """Start relaying messages between a server channel and a user's DMs."""
        if isinstance(ctx.channel, discord.DMChannel):
            return await ctx.send("This command can only be used in a server channel.")

        relays = await self.config.relays()
        if ctx.channel.id not in relays:
            relays[ctx.channel.id] = {"channel_id": ctx.channel.id, "user_id": user.id}
            await self.config.relays.set(relays)
            await ctx.send(f"Relay started between this channel and {user.display_name}'s DMs.")
        else:
            await ctx.send("A relay already exists for this channel.")

    @relaydm.command(name="stop")
    async def relaydm_stop(self, ctx):
        """Stop relaying messages between a server channel and a user's DMs."""
        relays = await self.config.relays()
        if ctx.channel.id in relays:
            del relays[ctx.channel.id]
            await self.config.relays.set(relays)
            await ctx.send("The relay has been stopped.")
        else:
            await ctx.send("No relay found for this channel.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # Check if the message is a bot command
        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return  # Ignore bot commands

        relays = await self.config.relays()

        # Check if the message is in a server channel with an active relay
        if isinstance(message.channel, discord.TextChannel) and message.channel.id in relays:
            relay_data = relays[message.channel.id]
            user = self.bot.get_user(relay_data["user_id"])
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

        # Check if the message is in a DM with an active relay
        elif isinstance(message.channel, discord.DMChannel):
            for relay_data in relays.values():
                if message.author.id == relay_data["user_id"]:
                    channel = self.bot.get_channel(relay_data["channel_id"])
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

def setup(bot):
    bot.add_cog(PrivateComm(bot))
