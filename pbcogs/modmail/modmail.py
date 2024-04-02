import discord
import asyncio
from discord.ext import commands
from discord_slash import SlashCommand, SlashContext

class ModMail(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.slash = SlashCommand(bot, sync_commands=True)
        self.mails_channel = None

    @slash.slash(name="setup", description="Set up modmail channel", guild_ids=[1234567890])
    @has_permissions(administrator=True)
    async def setup_slash(self, ctx: SlashContext):
        await ctx.trigger_typing()
        await asyncio.sleep(2)
        channel = discord.utils.get(ctx.guild.channels, name=config.mails_channel_name)
        if channel is None:
            guild = ctx.guild
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True)
            }
            try:
                self.mails_channel = await guild.create_text_channel(config.mails_channel_name, overwrites=overwrites)
            except:
                print("couldn't create a mod-logs channel, maybe it exists")

    @slash.slash(name="reply", description="Reply to modmail", guild_ids=[1234567890])
    async def reply_slash(self, ctx: SlashContext, id: int = 0, *, msg: str = "moderator is replying..."):
        user = self.bot.get_user(id)
        if user is not None:
            embed_reply = discord.Embed(
                title='Reply from Moderator',
                description=msg,
                color=discord.Color.blue()
            )
            await user.send(embed=embed_reply)



def setup(bot):
    bot.add_cog(ModMail(bot))


