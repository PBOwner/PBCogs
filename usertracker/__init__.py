
from redbot.core.bot import Red

from .usertracker import UserTracker

async def setup(bot: Red):
    await bot.add_cog(UserTracker(bot))
