import random
from redbot.core import commands
from redbot.core.bot import Red
import discord

class Praise(commands.Cog):
    """Praise Kink style cog for Red-DiscordBot"""

    def __init__(self, bot: Red):
        self.bot = bot
        self.praises = [
            "You have been so good!! Keep it up and we will see where you go!",
            "Amazing job! You're doing fantastic!",
            "Keep up the great work, superstar!",
            "You're on fire! Keep it going!",
            "You're doing an excellent job, keep it up!",
            "You're a rockstar! Keep shining!",
            "Fantastic effort! Keep up the good work!",
            "You're making great progress, keep it up!",
            "You're doing wonderfully, keep it going!",
            "You're a champ! Keep up the awesome work!"
        ]

    @commands.command()
    async def praise(self, ctx, target: discord.Member = None, *, custom_message: str = None):
        """Praise someone with a default or custom message."""
        if target is None and custom_message is None:
            await ctx.send("Please mention a user or provide a custom message.")
            return

        # Determine the user or role to praise
        if target is None:
            target = ctx.message.author

        # Fetch the target's most recent message
        async for message in ctx.channel.history(limit=100):
            if message.author == target:
                await message.add_reaction("⭐")
                break
        else:
            await ctx.send(f"Could not find a recent message from {target.display_name} in this channel.")
            return

        # Create the embed message
        title = f"Praising {target.display_name}"
        description = custom_message if custom_message else random.choice(self.praises)
        embed = discord.Embed(title=title, description=description, color=discord.Color.gold())

        # Send the embed message and ping the role if applicable
        if isinstance(target, discord.Role):
            await ctx.send(content=target.mention, embed=embed)
        else:
            await ctx.send(embed=embed)
