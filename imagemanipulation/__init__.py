
from redbot.core.bot import Red

from .imagemanipulation import ImageManipulation

async def setup(bot: Red):
    await bot.add_cog(ImageManipulation(bot))
