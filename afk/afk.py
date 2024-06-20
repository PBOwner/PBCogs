import discord
from redbot.core import commands, Config
from redbot.core.bot import Red

class AFK(commands.Cog):
    """AFK Cog for Red-DiscordBot"""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)

        default_global = {}
        default_guild = {"nickname_template": None}
        default_member = {"afk": False, "reason": None}

        self.config.register_global(**default_global)
        self.config.register_guild(**default_guild)
        self.config.register_member(**default_member)

    @commands.command()
    async def afk(self, ctx, *, reason: str = "No reason provided"):
        """Set your AFK status with an optional reason."""
        await self.config.member(ctx.author).afk.set(True)
        await self.config.member(ctx.author).reason.set(reason)

        nickname_template = await self.config.guild(ctx.guild).nickname_template()
        if nickname_template:
            new_nickname = nickname_template.format(displayname=ctx.author.display_name)
            try:
                await ctx.author.edit(nick=new_nickname)
            except discord.Forbidden:
                await ctx.send("I don't have permission to change your nickname.")
            except discord.HTTPException:
                await ctx.send("Failed to change your nickname.")

        await ctx.send(f"{ctx.author.mention} is now AFK. Reason: {reason}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        author_afk = await self.config.member(message.author).afk()
        if author_afk:
            await self.config.member(message.author).afk.set(False)
            await self.config.member(message.author).reason.set(None)

            try:
                await message.author.edit(nick=None)
            except discord.Forbidden:
                pass
            except discord.HTTPException:
                pass

            await message.channel.send(f"Welcome back, {message.author.mention}! I've removed your AFK status.")

        for mention in message.mentions:
            if mention == message.author:
                continue
            mention_afk = await self.config.member(mention).afk()
            if mention_afk:
                reason = await self.config.member(mention).reason()
                embed = discord.Embed(title="Pss. hey.", description=f"{mention.mention} is AFK! Their reason is: {reason}!")
                await message.channel.send(embed=embed)

    @commands.admin_or_permissions(manage_guild=True)
    @commands.command()
    async def setafknick(self, ctx, *, template: str = None):
        """Set a custom nickname template for AFK users. Use {displayname} as a placeholder for the user's display name."""
        await self.config.guild(ctx.guild).nickname_template.set(template)
        if template:
            await ctx.send(f"AFK nickname template set to: {template}")
        else:
            await ctx.send("AFK nickname template has been cleared.")

def setup(bot: Red):
    bot.add_cog(AFK(bot))
