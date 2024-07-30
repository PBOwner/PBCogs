from redbot.core.bot import Red

from .evalcog import EvalCog

async def setup(bot: Red):
    await bot.add_cog(EvalCog(bot))
