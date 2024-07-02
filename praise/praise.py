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

    @commands.group(invoke_without_command=True)
    async def praise(self, ctx, target: discord.Member = None, *, custom_message: str = None):
        """Praise a user with a default or custom message."""
        if target is None and custom_message is None:
            await ctx.send("Please mention a user or provide a custom message.")
            return

        # Fetch the target's most recent message
        last_message = None
        async for message in ctx.channel.history(limit=100):
            if message.author == target:
                last_message = message
                break

        # Create the embed message for the user
        title = f"Praising {target.display_name}"
        description = custom_message if custom_message else random.choice(list(self.praises.values()))
        embed = discord.Embed(title=title, description=description, color=discord.Color.gold())

        # Send the embed message
        await ctx.send(embed=embed)

        # Add a reaction to the last message if found
        if last_message:
            await last_message.add_reaction("⭐")

        # Send a DM to the user if they are not actively in the server
        if not ctx.guild.get_member(target.id):
            try:
                await target.send(embed=embed)
            except discord.Forbidden:
                await ctx.send(f"Could not send a DM to {target.display_name}.")

    @praise.command(name="role")
    async def praise_role(self, ctx, target: discord.Role, *, custom_message: str = None):
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

        # Praise each member in the role
        for member in target.members:
            # Fetch the member's most recent message
            last_message = None
            async for message in ctx.channel.history(limit=100):
                if message.author == member:
                    last_message = message
                    break

            # Send a DM to the member if they are not actively in the server
            if not ctx.guild.get_member(member.id):
                try:
                    await member.send(embed=embed)
                except discord.Forbidden:
                    await ctx.send(f"Could not send a DM to {member.display_name}.")
                continue

            # Add a reaction to the last message if found
            if last_message:
                await last_message.add_reaction("⭐")

            # Create the embed message for the member
            title = f"Praising {member.display_name}"
            description = custom_message if custom_message else random.choice(list(self.praises.values()))
            embed = discord.Embed(title=title, description=description, color=discord.Color.gold())

            # Send the embed message
            await ctx.send(embed=embed)

    @praise.command()
    async def add(self, ctx, *, new_praise: str):
        """Add a new praise message to the list."""
        praise_id = str(uuid.uuid4())
        self.praises[praise_id] = {"message": new_praise, "author": ctx.author.display_name}
        await ctx.send(f"Added new praise with ID {praise_id}: {new_praise}")

    @praise.command()
    async def remove(self, ctx, praise_id: str):
        """Remove a praise message by its UUID."""
        if praise_id in self.praises:
            removed_praise = self.praises.pop(praise_id)
            await ctx.send(f"Removed praise with ID {praise_id}: {removed_praise['message']}")
        else:
            await ctx.send(f"No praise found with ID {praise_id}")

    @praise.command()
    async def list(self, ctx):
        """List all praise messages."""
        if not self.praises:
            await ctx.send("No praises available.")
            return

        pages = []
        current_page = 0
        page_limit = 5  # Number of praises per page
        praises_list = list(self.praises.items())

        while current_page * page_limit < len(praises_list):
            embed = discord.Embed(title=f"Praises (Page {current_page + 1})", color=discord.Color.gold())
            for i in range(page_limit):
                if current_page * page_limit + i >= len(praises_list):
                    break
                praise_id, praise_info = praises_list[current_page * page_limit + i]
                embed.add_field(
                    name=f"Added by {praise_info['author']}",
                    value=f"{praise_info['message']}\n**UUID:** {praise_id}",
                    inline=False
                )
            pages.append(embed)
            current_page += 1

        for page in pages:
            await ctx.send(embed=page)
