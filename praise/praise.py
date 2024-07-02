from redbot.core import commands
from redbot.core.bot import Red
import discord

class Praise(commands.Cog):
    """Praise Kink style cog for Red-DiscordBot"""

    def __init__(self, bot: Red):
        self.bot = bot

    @commands.command()
    async def praise(self, ctx, user: discord.Member = None, *, custom_message: str = None):
        """Praise someone with a default or custom message."""
        if user is None and custom_message is None:
            await ctx.send("Please mention a user or provide a custom message.")
            return

        # Add star reaction to the message replied to
        if ctx.message.reference:
            ref_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            await ref_message.add_reaction("⭐")

        # Determine the user to praise
        if user is None:
            user = ctx.message.author

        # Create the embed message
        title = f"Praising {user.display_name}"
        description = custom_message if custom_message else "You have been so good!! Keep it up and we will see where you go!"
        embed = discord.Embed(title=title, description=description, color=discord.Color.gold())

        # Send the embed message
        await ctx.send(embed=embed)

def setup(bot: Red):
    bot.add_cog(Praise(bot))
