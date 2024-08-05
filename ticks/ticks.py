from redbot.core import commands, Config
from redbot.core.bot import Red
from discord.ext.commands import Context
from difflib import get_close_matches

class Ticks(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier: 1234567890)
        default_guild = {"tags": {}}
        self.config.register_guild(**default_guild)

    @commands.hybrid_group(name="ticks", invoke_without_command=True)
    async def ticks(self, ctx: commands.Context, name: str = None):
        """Base command for managing or using tags."""
        if name is None:
            await ctx.send("Use a subcommand to manage tags or provide a tag name to use a tag.")
        else:
            tags = await self.config.guild(ctx.guild).tags()
            if name in tags:
                await ctx.send(tags[name])
            else:
                close_matches = get_close_matches(name, tags.keys())
                if close_matches:
                    await ctx.send(f"Tag `{name}` not found. Did you mean `{close_matches[0]}`?")
                else:
                    await ctx.send(f"Tag `{name}` not found and no close matches were found.")

    @ticks.command(name="add")
    async def add(self, ctx: commands.Context, name: str, *, content: str):
        """Add a new tag."""
        async with self.config.guild(ctx.guild).tags() as tags:
            if name in tags:
                await ctx.send(f"The tag `{name}` already exists.")
                return
            tags[name] = content
        await ctx.send(f"Tag `{name}` added.")

    @ticks.command(name="remove")
    async def remove(self, ctx: commands.Context, name: str):
        """Remove an existing tag."""
        async with self.config.guild(ctx.guild).tags() as tags:
            if name not in tags:
                await ctx.send(f"The tag `{name}` does not exist.")
                return
            del tags[name]
        await ctx.send(f"Tag `{name}` removed.")

    @ticks.command(name="list")
    async def list(self, ctx: commands.Context):
        """List all tags."""
        tags = await self.config.guild(ctx.guild).tags()
        if not tags:
            await ctx.send("No tags available.")
            return
        tag_list = "\n".join(tags.keys())
        await ctx.send(f"Available tags:\n{tag_list}")
