from redbot.core.bot import Red

from .autodocsite import AutoDocSite

async def setup(bot: Red):
    await bot.add_cog(AutoDocSite(bot))
    await bot.add_cog(AutoDocs(bot))
