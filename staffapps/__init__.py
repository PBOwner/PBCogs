
from redbot.core.bot import Red

from .staffapps import StaffApps

async def setup(bot: Red):
    await bot.add_cog(StaffApps(bot))
