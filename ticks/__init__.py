from redbot.core.bot import Red

from .ticks import Ticks

async def setup(bot: Red):
    await bot.add_cog(Ticks(bot))
