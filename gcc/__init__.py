from redbot.core.bot import Red

from .gcc import GCC

async def setup(bot):
    await bot.add_cog(GCC(bot))
