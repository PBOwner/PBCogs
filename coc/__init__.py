from redbot.core.bot import Red

from .coc import COC

async def setup(bot):
    await bot.add_cog(COC(bot))
