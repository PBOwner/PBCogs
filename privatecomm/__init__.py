
from redbot.core.bot import Red

from .privatecomm import PrivateComm

async def setup(bot: Red):
    await bot.add_cog(PrivateComm(bot))
