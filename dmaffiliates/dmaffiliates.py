import discord
from redbot.core import commands, Config
from redbot.core.bot import Red

class DMAffiliates(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=9876543210)  # Replace with a unique identifier
        self.config.register_guild(affiliates=[])

    @commands.group()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def dmaffiliate(self, ctx):
        """Settings for the affiliate messages."""
        pass

    @dmaffiliate.command()
    async def add(self, ctx, *, message: str):
        """Add a new affiliate message."""
        async with self.config.guild(ctx.guild).affiliates() as affiliates:
            affiliates.append(message)
        await ctx.send("Affiliate message added.")

    @dmaffiliate.command()
    async def remove(self, ctx, index: int):
        """Remove an affiliate message by its index."""
        async with self.config.guild(ctx.guild).affiliates() as affiliates:
            if 0 <= index < len(affiliates):
                affiliates.pop(index)
                await ctx.send("Affiliate message removed.")
            else:
                await ctx.send("Invalid index.")

    @dmaffiliate.command()
    async def list(self, ctx):
        """List all affiliate messages."""
        affiliates = await self.config.guild(ctx.guild).affiliates()
        if affiliates:
            messages = "\n".join(f"{i+1}. {message}" for i, message in enumerate(affiliates))
            await ctx.send(f"Affiliate Messages:\n{messages}")
        else:
            await ctx.send("No affiliate messages set.")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Send affiliate messages to a new member."""
        affiliates = await self.config.guild(member.guild).affiliates()
        if affiliates:
            for message in affiliates:
                try:
                    await member.send(message)
                except discord.Forbidden:
                    # Handle the case where the bot can't send a DM to the user
                    pass
