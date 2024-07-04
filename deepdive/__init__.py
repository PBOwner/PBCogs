from redbot.core.bot import Red

from .deepdive import DeepDive

async def setup(bot: Red):
    await bot.add_cog(DeepDive(bot))
