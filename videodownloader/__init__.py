
from redbot.core.bot import Red

from .videodownloader import VideoDownloader

async def setup(bot: Red):
    await bot.add_cog(VideoDownloader(bot))
