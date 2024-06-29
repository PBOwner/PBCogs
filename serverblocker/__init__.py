from redbot.core.bot import Red

from .serverblocker import ServerBlocker

async def setup(bot):
    await bot.add_cog(ServerBlocker(bot))
