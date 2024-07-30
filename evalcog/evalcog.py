import discord
from redbot.core import commands
from discord.http import Route
import traceback
import textwrap

class EvalCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.is_owner()  # Ensure only the bot owner can run this command
    @commands.command(name='eval')
    async def _eval(self, ctx, *, code: str):
        try:
            # Prepare the environment for eval
            env = {
                'bot': self.bot,
                'ctx': ctx,
                'discord': discord,
                'commands': commands,
                'Route': Route,
                '__import__': __import__
            }
            # Define a function to execute the code
            exec_code = f'async def __eval_func():\n{textwrap.indent(code, "    ")}'
            exec(exec_code, env)
            # Execute the function and get the result
            result = await env['__eval_func']()
            await ctx.send(f'```{result}```')
        except Exception as e:
            # Send the traceback in case of an error
            await ctx.send(f'```{traceback.format_exc()}```')

def setup(bot):
    bot.add_cog(EvalCog(bot))
