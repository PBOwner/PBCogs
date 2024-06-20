from redbot.core.bot import Red

from .gametracker import GameTracker

async def setup(bot):
    await bot.add_cog(GameTracker(bot))
