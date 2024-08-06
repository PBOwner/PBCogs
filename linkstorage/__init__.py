from redbot.core.bot import Red

from .linkstorage import LinkStorage

async def setup(bot: Red):
    await bot.add_cog(LinkStorage(bot))
