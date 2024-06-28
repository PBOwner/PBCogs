

from redbot.core.bot import Red

from .advancedinvitetracker import AdvancedInviteTracker

async def setup(bot: Red):
    await bot.add_cog(AdvancedInviteTracker(bot))
