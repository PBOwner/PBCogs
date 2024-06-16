from redbot.core.bot import Red

from .restartmsg import RestartMsg

async def setup(bot):
    await bot.add_cog(RestartMsg(bot))
