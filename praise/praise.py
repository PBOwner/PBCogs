import random
import uuid
from redbot.core import commands
from redbot.core.bot import Red
import discord

class Praise(commands.Cog):
    """Praise Kink style cog for Red-DiscordBot"""

    def __init__(self, bot: Red):
        self.bot = bot
        self.praises = {
            str(uuid.uuid4()): "You have been so good!! Keep it up and we will see where you go!",
            str(uuid.uuid4()): "Amazing job! You're doing fantastic!",
            str(uuid.uuid4()): "Keep up the great work, superstar!",
            str(uuid.uuid4()): "You're on fire! Keep it going!",
            str(uuid.uuid4()): "You're doing an excellent job, keep it up!",
            str(uuid.uuid4()): "You're a rockstar! Keep shining!",
            str(uuid.uuid4()): "Fantastic effort! Keep up the good work!",
            str(uuid.uuid4()): "You're making great progress, keep it up!",
            str(uuid.uuid4()): "You're doing wonderfully, keep it going!",
            str(uuid.uuid4()): "You're a champ! Keep up the awesome work!"
        }

    @commands.group()
    async def praise(self, ctx):
        """Praise commands."""
        pass

    @praise.command()
    async def add(self, ctx, *, new_praise: str):
        """Add a new praise message to the list."""
        praise_id = str(uuid.uuid4())
        self.praises[praise_id] = new_praise
        await ctx.send(f"Added new praise with ID {praise_id}: {new_praise}")

    @praise.command()
    async def remove(self, ctx, praise_id: str):
        """Remove a praise message by its UUID."""
        if praise_id in self.praises:
            removed_praise = self.praises.pop(praise_id)
            await ctx.send(f"Removed praise with ID {praise_id}: {removed_praise}")
        else:
            await ctx.send(f"No praise found with ID {praise_id}")

    @praise.command()
    async def list(self, ctx):
        """List all praise messages."""
        if not self.praises:
            await ctx.send("No praises available.")
            return

        praise_list = "\n".join(f"{praise_id}: {praise}" for praise_id, praise in self.praises.items())
        await ctx.send(f"Current praises:\n{praise_list}")

    @praise.command()
    async def user(self, ctx, target: discord.Member, *, custom_message: str = None):
        """Praise a user with a default or custom message."""
        if target is None and custom_message is None:
            await ctx.send("Please mention a user or provide a custom message.")
            return

        # Fetch the target's most recent message
        async for message in ctx.channel.history(limit=100):
            if message.author == target:
                await message.add_reaction("⭐")
                break
        else:
            await ctx.send(f"Could not find a recent message from {target.display_name} in this channel.")
            return

        # Create the embed message for the user
        title = f"Praising {target.display_name}"
        description = custom_message if custom_message else random.choice(list(self.praises.values()))
        embed = discord.Embed(title=title, description=description, color=discord.Color.gold())

        # Send the embed message
        await ctx.send(embed=embed)

    @praise.command()
    async def role(self, ctx, target: discord.Role, *, custom_message: str = None):
        """Praise a role with a default or custom message."""
        if target is None and custom_message is None:
            await ctx.send("Please mention a role or provide a custom message.")
            return

        # Create the embed message for the role
        title = f"Praising {target.name}"
        description = custom_message if custom_message else random.choice(list(self.praises.values()))
        embed = discord.Embed(title=title, description=description, color=discord.Color.gold())

        # Send the embed message and ping the role
        await ctx.send(content=target.mention, embed=embed)
