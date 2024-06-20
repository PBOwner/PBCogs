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
        default_member = {"afk": False, "reason": None, "embed_color": None}

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
                await ctx.send(embed=self.create_embed(ctx.author, "I don't have permission to change your nickname."))
            except discord.HTTPException:
                await ctx.send(embed=self.create_embed(ctx.author, "Failed to change your nickname."))

        await ctx.send(embed=self.create_embed(ctx.author, f"{ctx.author.mention} is now AFK. Reason: {reason}"))

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

            await message.channel.send(embed=self.create_embed(message.author, f"Welcome back, {message.author.mention}! I've removed your AFK status."))

        for mention in message.mentions:
            if mention == message.author:
                continue
            mention_afk = await self.config.member(mention).afk()
            if mention_afk:
                reason = await self.config.member(mention).reason()
                embed = discord.Embed(title="Pss. hey.", description=f"{mention.mention} is AFK! Their reason is: {reason}!", color=await self.get_embed_color(mention))
                await message.channel.send(embed=embed)

    @commands.admin_or_permissions(manage_guild=True)
    @commands.command()
    async def setafknick(self, ctx, *, template: str = None):
        """Set a custom nickname template for AFK users. Use {displayname} as a placeholder for the user's display name."""
        await self.config.guild(ctx.guild).nickname_template.set(template)
        if template:
            await ctx.send(embed=self.create_embed(ctx.author, f"AFK nickname template set to: {template}"))
        else:
            await ctx.send(embed=self.create_embed(ctx.author, "AFK nickname template has been cleared."))

    @commands.command()
    async def setafkcolor(self, ctx, color: discord.Color):
        """Set the embed color for AFK messages."""
        await self.config.member(ctx.author).embed_color.set(color.value)
        await ctx.send(embed=self.create_embed(ctx.author, f"AFK embed color set to: {color}"))

    async def get_embed_color(self, user: discord.Member):
        color_value = await self.config.member(user).embed_color()
        if color_value:
            return discord.Color(color_value)
        else:
            return discord.Color.default()

    def create_embed(self, user: discord.Member, description: str):
        color = await self.get_embed_color(user)
        embed = discord.Embed(description=description, color=color)
        return embed

def setup(bot: Red):
    bot.add_cog(AFK(bot))
