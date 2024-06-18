from redbot.core.bot import Red

from .xenon import Xenon 

async def setup(bot):
    """Setup the Xenon cog."""
    await bot.add_cog(Xenon(bot))
