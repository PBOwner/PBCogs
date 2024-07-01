
from redbot.core.bot import Red

from .supportbuddy import SupportBuddy

async def setup(bot: Red):
    await bot.add_cog(SupportBuddy(bot))
