from redbot.core import commands, Config
import discord
from redbot.core.bot import Red

class GCC(commands.Cog):
    """A cog to add custom commands to the bot globally"""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_global = {
            "commands": {}
        }
        self.config.register_global(**default_global)

    @commands.group(invoke_without_command=True)
    @commands.is_owner()
    async def gcc(self, ctx):
        """Group command for managing custom commands"""
        embed = discord.Embed(title="GCC Commands", color=discord.Color.blue())
        embed.add_field(name="Add Command", value="`gcc add <command_name> <response>`", inline=False)
        embed.add_field(name="Remove Command", value="`gcc remove <command_name>`", inline=False)
        await ctx.send(embed=embed)

    @gcc.command()
    async def add(self, ctx, name: str, *, response: str):
        """Add a custom command"""
        async with self.config.commands() as commands:
            if name in commands:
                await ctx.send(f"A custom command with the name `{name}` already exists.")
                return
            commands[name] = response
            await ctx.send(f"Custom command `{name}` added successfully.")

    @gcc.command()
    async def remove(self, ctx, name: str):
        """Remove a custom command"""
        async with self.config.commands() as commands:
            if name not in commands:
                await ctx.send(f"No custom command found with the name `{name}`.")
                return
            del commands[name]
            await ctx.send(f"Custom command `{name}` removed successfully.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return

        async with self.config.commands() as commands:
            prefix = await self.bot.get_prefix(message)
            if isinstance(prefix, list):
                prefix = prefix[0]
            command_name = message.content[len(prefix):].split()[0]
            if command_name in commands:
                await message.channel.send(commands[command_name])

def setup(bot):
    bot.add_cog(GCC(bot))
