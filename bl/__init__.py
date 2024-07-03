
from redbot.core.bot import Red

from .bl import Bl

async def setup(bot: Red):
    await bot.add_cog(Bl(bot))
