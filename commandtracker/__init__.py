from redbot.core.bot import Red

from .commandtracker import CommandTracker

async def setup(bot):
    await bot.add_cog(CommandTracker(bot))
