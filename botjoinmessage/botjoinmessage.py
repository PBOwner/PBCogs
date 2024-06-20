import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
from typing import Optional

class BotJoinMessage(commands.Cog):
    """Cog to send a configurable message to the server owner when the bot joins a server."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567891, force_registration=True)
        default_global = {
            "title": "Welcome!",
            "fields": [],
            "color": discord.Color.blue().value
        }
        self.config.register_global(**default_global)
        self.current_embed_message = None

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        owner = guild.owner
        if owner:
            title = await self.config.title()
            fields = await self.config.fields()
            color = discord.Color(await self.config.color())

            embed = discord.Embed(
                title=title,
                color=color
            )
            for field in fields:
                embed.add_field(name=field["name"], value=field["value"], inline=field["inline"])

            try:
                await owner.send(embed=embed)
            except discord.Forbidden:
                pass

    @commands.is_owner()
    @commands.group(aliases=["bjm"])
    async def botjoinmessage(self, ctx: commands.Context):
        """Commands to configure the bot join message."""
        pass

    @botjoinmessage.command()
    async def settitle(self, ctx: commands.Context, *, title: str):
        """Set the title of the bot join message."""
        await self.config.title.set(title)
        await ctx.send(f"Title set to: {title}")
        await self._update_current_embed(ctx)

    @botjoinmessage.command()
    async def addfield(self, ctx: commands.Context, name: str, value: str, inline: Optional[bool] = True):
        """Add a field to the bot join message."""
        async with self.config.fields() as fields:
            fields.append({"name": name, "value": value, "inline": inline})
        await ctx.send(f"Field added: {name} - {value}")
        await self._update_current_embed(ctx)

    @botjoinmessage.command()
    async def editfield(self, ctx: commands.Context, index: int, name: Optional[str] = None, value: Optional[str] = None, inline: Optional[bool] = None):
        """Edit a field in the bot join message."""
        async with self.config.fields() as fields:
            if 0 <= index < len(fields):
                if name:
                    fields[index]["name"] = name
                if value:
                    fields[index]["value"] = value
                if inline is not None:
                    fields[index]["inline"] = inline
                await ctx.send(f"Field {index} edited.")
                await self._update_current_embed(ctx)
            else:
                await ctx.send(f"Field at index {index} does not exist.")

    @botjoinmessage.command()
    async def removefield(self, ctx: commands.Context, index: int):
        """Remove a field from the bot join message."""
        async with self.config.fields() as fields:
            if 0 <= index < len(fields):
                fields.pop(index)
                await ctx.send(f"Field {index} removed.")
                await self._update_current_embed(ctx)
            else:
                await ctx.send(f"Field at index {index} does not exist.")

    @botjoinmessage.command()
    async def listfields(self, ctx: commands.Context):
        """List all fields in the bot join message."""
        fields = await self.config.fields()
        if fields:
            embed = discord.Embed(
                title="Bot Join Message Fields",
                color=discord.Color.blue()
            )
            for index, field in enumerate(fields):
                embed.add_field(name=f"Field {index}", value=f"**Name:** {field['name']}\n**Value:** {field['value']}\n**Inline:** {field['inline']}", inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send("No fields set.")

    @botjoinmessage.command()
    async def setcolor(self, ctx: commands.Context, color: discord.Color):
        """Set the color of the bot join message."""
        await self.config.color.set(color.value)
        await ctx.send(f"Color set to: {color}")
        await self._update_current_embed(ctx)

    @botjoinmessage.command()
    async def preview(self, ctx: commands.Context):
        """Preview the current bot join message."""
        title = await self.config.title()
        fields = await self.config.fields()
        color = discord.Color(await self.config.color())

        embed = discord.Embed(
            title=title,
            color=color
        )
        for field in fields:
            embed.add_field(name=field["name"], value=field["value"], inline=field["inline"])

        self.current_embed_message = await ctx.send(embed=embed)

    async def _update_current_embed(self, ctx: commands.Context):
        """Update the current embed message with the latest configuration."""
        if self.current_embed_message:
            title = await self.config.title()
            fields = await self.config.fields()
            color = discord.Color(await self.config.color())

            embed = discord.Embed(
                title=title,
                color=color
            )
            for field in fields:
                embed.add_field(name=field["name"], value=field["value"], inline=field["inline"])

            try:
                await self.current_embed_message.edit(embed=embed)
            except discord.NotFound:
                self.current_embed_message = None
            except discord.Forbidden:
                await ctx.send("I don't have permission to edit the message.")

def setup(bot: Red):
    bot.add_cog(BotJoinMessage(bot))
