from redbot.core.bot import Red

from .presencefetcher import PresenceFetcher

async def setup(bot):
    await bot.add_cog(PresenceFetcher(bot))
