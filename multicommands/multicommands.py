from redbot.core import commands
import asyncio

class MultiCommands(commands.Cog):
    """Cog to execute multiple commands separated by &&"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def multi(self, ctx, *, commands_str: str):
        """Execute multiple commands separated by &&"""
        commands_list = commands_str.split("&&")
        for command in commands_list:
            command = command.strip()
            if command:
                msg = ctx.message
                msg.content = ctx.prefix + command
                new_ctx = await self.bot.get_context(msg)
                await self.bot.invoke(new_ctx)
                await asyncio.sleep(1)  # Adding a small delay to avoid rate limits

def setup(bot):
    bot.add_cog(MultiCommands(bot))
