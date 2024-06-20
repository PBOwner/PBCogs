from redbot.core.bot import Red

from .presencetracker import PresenceTracker

async def setup(bot):
    await bot.add_cog(PresenceTracker(bot))
