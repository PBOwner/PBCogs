from redbot.core.bot import Red

from .comm import Comm

async def setup(bot):
    await bot.add_cog(Comm(bot))
