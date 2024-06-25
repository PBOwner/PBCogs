from redbot.core.bot import Red

from .botlogger import BotLogger

async def setup(bot: Red):
    await bot.add_cog(BotLogger(bot))
