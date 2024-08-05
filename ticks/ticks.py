from redbot.core import commands, Config
from redbot.core.bot import Red
from discord.ext.commands import Context
from difflib import get_close_matches
import discord
import random

class Ticks(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {"tags": {}}
        self.config.register_guild(**default_guild)

    @commands.hybrid_group(name="ticks", invoke_without_command=True)
    async def ticks(self, ctx: commands.Context):
        """Base command for managing or using tags."""
        embed = discord.Embed(
            description="Use a subcommand to manage tags or use `ticks run` to execute a tag.",
            color=discord.Color.blue()
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

    @ticks.command(name="run")
    async def run(self, ctx: commands.Context, tag: str):
        """Run a tag."""
        tags = await self.config.guild(ctx.guild).tags()
        if tag in tags:
            color = discord.Color(random.randint(0, 0xFFFFFF))
            embed = discord.Embed(
                description=tags[tag],
                color=color
            )
            await ctx.send(embed=embed)
        else:
            close_matches = get_close_matches(tag, tags.keys())
            if close_matches:
                embed = discord.Embed(
                    description=f"Tag `{tag}` not found. Did you mean `{close_matches[0]}`?",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    description=f"Tag `{tag}` not found and no close matches were found.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)

    @run.autocomplete("tag")
    async def autocomplete_tag(self, interaction: discord.Interaction, current: str):
        tags = await self.config.guild(interaction.guild).tags()
        return [tag for tag in tags if current.lower() in tag.lower()]
