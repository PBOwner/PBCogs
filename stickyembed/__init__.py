
from redbot.core.bot import Red

from .stickyembed import StickyEmbed

async def setup(bot: Red):
    await bot.add_cog(StickyEmbed(bot))
