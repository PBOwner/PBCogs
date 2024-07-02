from redbot.core.bot import Red

from .nsfwbdsm import NSFWBDSM

async def setup(bot: Red):
    await bot.add_cog(NSFWBDSM(bot))
