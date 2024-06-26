from redbot.core.bot import Red

from .globallogger import GlobalLogger

async def setup(bot: Red):
    await bot.add_cog(GlobalLogger(bot))
