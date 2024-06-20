import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
from typing import List, Dict

class AFK(commands.Cog):
    """AFK Cog for FuturoBot"""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)

        default_global = {}
        default_guild = {"nickname_template": None}
        default_user = {"afk": False, "reason": None, "embed_color": None, "mentions": []}

        self.config.register_global(**default_global)
        self.config.register_guild(**default_guild)
        self.config.register_user(**default_user)

    @commands.command()
    async def afk(self, ctx, *, reason: str = "No reason provided"):
        """Set your AFK status with an optional reason."""
        await self.config.user(ctx.author).afk.set(True)
        await self.config.user(ctx.author).reason.set(reason)
        await self.config.user(ctx.author).mentions.set([])  # Clear previous mentions

        nickname_template = await self.config.guild(ctx.guild).nickname_template()
        if nickname_template:
            new_nickname = nickname_template.format(displayname=ctx.author.display_name)
            try:
                await ctx.author.edit(nick=new_nickname)
            except discord.Forbidden:
                await ctx.send(embed=await self.create_embed(ctx.author, "I don't have permission to change your nickname."))
            except discord.HTTPException:
                await ctx.send(embed=await self.create_embed(ctx.author, "Failed to change your nickname."))

        await ctx.send(embed=await self.create_embed(ctx.author, f"{ctx.author.mention} is now AFK. Reason: {reason}"))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        author_afk = await self.config.user(message.author).afk()
        if author_afk:
            await self.config.user(message.author).afk.set(False)
            await self.config.user(message.author).reason.set(None)

            mentions = await self.config.user(message.author).mentions()
            if mentions:
                embed = discord.Embed(title="AFK Mentions", color=await self.get_embed_color(message.author))
                for mention in mentions:
                    embed.add_field(name=f"Mentioned by {mention['author']}", value=f"[Jump to message]({mention['link']})", inline=False)
            else:
                embed = discord.Embed(title="AFK Mentions", description="No pings were sent during your AFK.", color=await self.get_embed_color(message.author))

            await message.channel.send(embed=embed)
            await self.config.user(message.author).mentions.set([])  # Clear mentions after sending

            try:
                await message.author.edit(nick=None)
            except discord.Forbidden:
                pass
            except discord.HTTPException:
                pass

            await message.channel.send(embed=await self.create_embed(message.author, f"Welcome back, {message.author.mention}! I've removed your AFK status."))

        for mention in message.mentions:
            if mention == message.author:
                continue
            mention_afk = await self.config.user(mention).afk()
            if mention_afk:
                reason = await self.config.user(mention).reason()
                embed = discord.Embed(title=f"Psst. Hey, {message.author.name}", color=await self.get_embed_color(mention))
                embed.add_field(name="User", value=mention.mention, inline=False)
                embed.add_field(name="Reason", value=reason, inline=False)
                await message.channel.send(embed=embed)

                # Save the mention details
                mentions = await self.config.user(mention).mentions()
                mentions.append({"author": message.author.name, "link": message.jump_url})
                await self.config.user(mention).mentions.set(mentions)

    @commands.admin_or_permissions(manage_guild=True)
    @commands.command()
    async def setafknick(self, ctx, *, template: str = None):
        """Set a custom nickname template for AFK users. Use {displayname} as a placeholder for the user's display name."""
        await self.config.guild(ctx.guild).nickname_template.set(template)
        if template:
            await ctx.send(embed=await self.create_embed(ctx.author, f"AFK nickname template set to: {template}"))
        else:
            await ctx.send(embed=await self.create_embed(ctx.author, "AFK nickname template has been cleared."))

    @commands.command()
    async def setafkcolor(self, ctx, color: discord.Color):
        """Set the embed color for AFK messages."""
        await self.config.user(ctx.author).embed_color.set(color.value)
        await ctx.send(embed=await self.create_embed(ctx.author, f"AFK embed color set to: {color}"))

    async def get_embed_color(self, user: discord.User):
        color_value = await self.config.user(user).embed_color()
        if color_value:
            return discord.Color(color_value)
        else:
            return discord.Color.default()

    async def create_embed(self, user: discord.User, description: str):
        color = await self.get_embed_color(user)
        embed = discord.Embed(description=description, color=color)
        return embed

def setup(bot: Red):
    bot.add_cog(AFK(bot))
