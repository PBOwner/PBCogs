
from redbot.core.bot import Red

from .affiliatedservers import AffiliatedServers

async def setup(bot: Red):
    await bot.add_cog(AffiliatedServers(bot))
