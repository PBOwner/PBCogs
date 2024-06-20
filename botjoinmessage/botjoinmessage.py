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
            "fields": []
        }
        self.config.register_global(**default_global)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        owner = guild.owner
        if owner:
            title = await self.config.title()
            fields = await self.config.fields()

            embed = discord.Embed(
                title=title,
                color=discord.Color.blue()
            )
            for field in fields:
                embed.add_field(name=field["name"], value=field["value"], inline=field["inline"])

            try:
                await owner.send(embed=embed)
            except discord.Forbidden:
                pass

    @commands.is_owner()
    @commands.group()
    async def botjoinmessage(self, ctx: commands.Context):
        """Commands to configure the bot join message."""
        pass

    @botjoinmessage.command()
    async def settitle(self, ctx: commands.Context, *, title: str):
        """Set the title of the bot join message."""
        await self.config.title.set(title)
        await ctx.send(f"Title set to: {title}")

    @botjoinmessage.command()
    async def addfield(self, ctx: commands.Context, name: str, value: str, inline: Optional[bool] = True):
        """Add a field to the bot join message."""
        async with self.config.fields() as fields:
            fields.append({"name": name, "value": value, "inline": inline})
        await ctx.send(f"Field added: {name} - {value}")

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
            else:
                await ctx.send(f"Field at index {index} does not exist.")

    @botjoinmessage.command()
    async def removefield(self, ctx: commands.Context, index: int):
        """Remove a field from the bot join message."""
        async with self.config.fields() as fields:
            if 0 <= index < len(fields):
                fields.pop(index)
                await ctx.send(f"Field {index} removed.")
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

def setup(bot: Red):
    bot.add_cog(BotJoinMessage(bot))
