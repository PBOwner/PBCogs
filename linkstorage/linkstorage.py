import discord
from redbot.core import commands, Config
from redbot.core.bot import Red

class LinkStorage(commands.Cog):
    """A cog to store and retrieve links by name."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567891)
        self.config.register_global(links={})

    @commands.group()
    async def link(self, ctx: commands.Context):
        """Group command for managing links."""
        pass

    @link.command()
    @commands.is_owner()
    async def add(self, ctx: commands.Context, name: str, link: str):
        """Add a link to the storage."""
        async with self.config.links() as links:
            links[name] = link
        await ctx.send(f"Added link: {name} -> {link}")

    @link.command()
    @commands.is_owner()
    async def remove(self, ctx: commands.Context, name: str):
        """Remove a link from the storage."""
        async with self.config.links() as links:
            if name in links:
                del links[name]
                await ctx.send(f"Removed link: {name}")
            else:
                await ctx.send(f"No link found with the name: {name}")

    @link.command()
    async def get(self, ctx: commands.Context, name: str):
        """Retrieve a link by name."""
        links = await self.config.links()
        if name in links:
            await ctx.send(f"{name} -> {links[name]}")
        else:
            await ctx.send(f"No link found with the name: {name}")

    @link.command()
    async def list(self, ctx: commands.Context):
        """List all stored links."""
        links = await self.config.links()
        if links:
            description = "\n".join([f"{name} -> {link}" for name, link in links.items()])
            embed = discord.Embed(description=description, color=discord.Color.blue())
            await ctx.send(embed=embed)
        else:
            await ctx.send("No links stored.")
