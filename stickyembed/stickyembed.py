import discord
from redbot.core import commands

class StickyEmbed(commands.Cog):
    """A cog for creating sticky embeds."""

    def __init__(self, bot):
        self.bot = bot
        self.sticky_message = None
        self.sticky_channel = None
        self.embed = None
        self.stop = False

    @commands.command()
    async def esticky(self, ctx, title: str, description: str, color: discord.Color, footer: str = None, *fields: str):
        """Create a customizable sticky embed.

        Parameters:
        - title: The title of the embed.
        - description: The description of the embed.
        - color: The color of the embed (e.g., #3498db).
        - footer: The footer text of the embed (optional).
        - fields: Optional fields in the format name:value.
        """
        embed = discord.Embed(
            title=title,
            description=description,
            color=color
        )

        # Add fields to the embed if provided
        for field in fields:
            if ':' in field:
                name, value = field.split(":", 1)
                embed.add_field(name=name.strip(), value=value.strip(), inline=False)

        # Set the footer if provided
        if footer:
            embed.set_footer(text=footer)

        # Store the embed and channel for later use
        self.embed = embed
        self.sticky_channel = ctx.channel
        self.stop = False

        # Send the initial embed to the channel
        self.sticky_message = await ctx.send(embed=embed)

    @commands.command()
    async def unesticky(self, ctx):
        """Stop the sticky embed from updating."""
        if self.sticky_channel and self.sticky_message:
            self.stop = True
            await ctx.send("Sticky embed has been stopped from updating.")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listener to keep the embed at the bottom."""
        if self.sticky_channel and message.channel == self.sticky_channel and not message.author.bot and not self.stop:
            await self.sticky_message.delete()
            self.sticky_message = await self.sticky_channel.send(embed=self.embed)
