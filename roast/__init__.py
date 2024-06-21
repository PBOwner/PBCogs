from redbot.core.bot import Red

from .roast import Roast

async def setup(bot):
    await bot.add_cog(Roast(bot))
