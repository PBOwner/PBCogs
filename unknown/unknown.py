from redbot.core import commands, Config
import discord
from redbot.core.bot import Red

class Unknown(commands.Cog):
    """A cog to handle invalid commands with a custom error message"""

    def __init__(self, bot: Red):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            prefix = (await self.bot.get_valid_prefixes(ctx.guild))[0]
            embed = discord.Embed(title="ErRoR 404", color=discord.Color.red())
            embed.add_field(name="Error", value=f"Sorry, but `{ctx.invoked_with}` is not a valid command. Please use `{prefix}help` to display all commands.", inline=False)
            await ctx.send(f"{ctx.author.mention}", embed=embed)
        else:
            # Re-raise the error if it is not a CommandNotFound error
            raise error

def setup(bot):
    bot.add_cog(Unknown(bot))
