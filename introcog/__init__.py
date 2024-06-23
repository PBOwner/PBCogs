
from redbot.core.bot import Red

from .introcog import IntroCog

async def setup(bot: Red):
    await bot.add_cog(IntroCog(bot))
