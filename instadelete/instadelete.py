import discord
from redbot.core import commands, Config

class InstaDelete(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {}
        self.config.register_guild(**default_guild)

    @commands.command()
    async def toggleinstadelete(self, ctx):
        """Toggle instant deletion of commands for the user in the current server."""
        user = ctx.author
        guild = ctx.guild
        current = await self.config.guild(guild).get_raw(user.id, default=False)
        await self.config.guild(guild).set_raw(user.id, value=not current)
        status = "enabled" if not current else "disabled"
        await ctx.send(f"Instant deletion of commands has been {status} for {user.display_name} in this server.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild:
            return  # Ignore DMs

        user = message.author
        guild = message.guild
        if user.bot:
            return  # Ignore bot messages

        ctx = await self.bot.get_context(message)
        if ctx.valid:
            insta_delete = await self.config.guild(guild).get_raw(user.id, default=False)
            if insta_delete:
                # Check for mentions
                if message.mentions or message.role_mentions:
                    mention_text = " ".join([mention.mention for mention in message.mentions + message.role_mentions])
                    await message.channel.send(f"{mention_text}")

                await message.delete()
