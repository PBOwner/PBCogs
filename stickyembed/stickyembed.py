import discord
from redbot.core import commands

class StickyEmbed(commands.Cog):
    """A cog for creating sticky embeds."""

    def __init__(self, bot):
        self.bot = bot
        self.sticky_message = None
        self.sticky_channel = None
        self.embed = None

    @commands.command()
    async def esticky(self, ctx, title: str, description: str, footer: str, *fields: str):
        """Create a customizable sticky embed."""
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blue()  # You can customize the color if needed
        )

        # Add fields to the embed if provided
        for field in fields:
            if ':' in field:
                name, value = field.split(":", 1)
                embed.add_field(name=name.strip(), value=value.strip(), inline=False)

        # Set the footer
        embed.set_footer(text=footer)

        # Store the embed and channel for later use
        self.embed = embed
        self.sticky_channel = ctx.channel

        # Send the initial embed to the channel
        self.sticky_message = await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listener to keep the embed at the bottom."""
        if self.sticky_channel and message.channel == self.sticky_channel and not message.author.bot:
            await self.sticky_message.delete()
            self.sticky_message = await self.sticky_channel.send(embed=self.embed)
