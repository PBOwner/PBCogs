
from redbot.core.bot import Red

from .dmaffiliates import DMAffiliates

async def setup(bot: Red):
    await bot.add_cog(DMAffiliates(bot))
