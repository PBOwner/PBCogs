
from redbot.core.bot import Red

from .advancedlogger import AdvancedLogger

async def setup(bot: Red):
    await bot.add_cog(AdvancedLogger(bot))
