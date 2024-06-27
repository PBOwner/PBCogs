
from redbot.core.bot import Red

from .googlesearch import GoogleSearch

async def setup(bot: Red):
    await bot.add_cog(GoogleSearch(bot))
