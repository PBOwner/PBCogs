from redbot.core.bot import Red

from .instadelete import InstaDelete

async def setup(bot: Red):
    await bot.add_cog(InstaDelete(bot))
