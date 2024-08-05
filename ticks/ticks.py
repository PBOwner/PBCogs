from redbot.core import commands, Config
from redbot.core.bot import Red
from discord.ext.commands import Context
from difflib import get_close_matches
import discord

class Ticks(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {"tags": {}}
        self.config.register_guild(**default_guild)

    @commands.hybrid_group(name="ticks", invoke_without_command=True)
    async def ticks(self, ctx: commands.Context, name: str = None, options: str = None):
        """Base command for managing or using tags."""
        if name is None:
            if options is None:
                embed = discord.Embed(
                    description="Use a subcommand to manage tags or provide a tag name to use a tag.",
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)
            else:
                tags = await self.config.guild(ctx.guild).tags()
                if options in tags:
                    embed = discord.Embed(
                        description=tags[options],
                        color=discord.Color.green()
                    )
                    await ctx.send(embed=embed)
                else:
                    close_matches = get_close_matches(options, tags.keys())
                    if close_matches:
                        embed = discord.Embed(
                            description=f"Tag `{options}` not found. Did you mean `{close_matches[0]}`?",
                            color=discord.Color.red()
                        )
                        await ctx.send(embed=embed)
                    else:
                        embed = discord.Embed(
                            description=f"Tag `{options}` not found and no close matches were found.",
                            color=discord.Color.red()
                        )
                        await ctx.send(embed=embed)
        else:
            tags = await self.config.guild(ctx.guild).tags()
            if name in tags:
                embed = discord.Embed(
                    description=tags[name],
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
            else:
                close_matches = get_close_matches(name, tags.keys())
                if close_matches:
                    embed = discord.Embed(
                        description=f"Tag `{name}` not found. Did you mean `{close_matches[0]}`?",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(
                        description=f"Tag `{name}` not found and no close matches were found.",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=embed)

    @ticks.command(name="add")
    async def add(self, ctx: commands.Context, name: str, *, content: str):
        """Add a new tag."""
        async with self.config.guild(ctx.guild).tags() as tags:
            if name in tags:
                embed = discord.Embed(
                    description=f"The tag `{name}` already exists.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            tags[name] = content
        embed = discord.Embed(
            description=f"Tag `{name}` added.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @ticks.command(name="remove")
    async def remove(self, ctx: commands.Context, name: str):
        """Remove an existing tag."""
        async with self.config.guild(ctx.guild).tags() as tags:
            if name not in tags:
                embed = discord.Embed(
                    description=f"The tag `{name}` does not exist.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            del tags[name]
        embed = discord.Embed(
            description=f"Tag `{name}` removed.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @ticks.command(name="list")
    async def list(self, ctx: commands.Context):
        """List all tags."""
        tags = await self.config.guild(ctx.guild).tags()
        if not tags:
            embed = discord.Embed(
                description="No tags available.",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            return
        tag_list = "\n".join(tags.keys())
        embed = discord.Embed(
            description=f"Available tags:\n{tag_list}",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
