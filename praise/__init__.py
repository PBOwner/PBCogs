from redbot.core.bot import Red

from .praise import Praise

async def setup(bot: Red):
    await bot.add_cog(Praise(bot))
