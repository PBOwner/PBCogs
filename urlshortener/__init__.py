
from redbot.core.bot import Red

from .urlshortener import URLShortener

async def setup(bot: Red):
    await bot.add_cog(URLShortener(bot))
