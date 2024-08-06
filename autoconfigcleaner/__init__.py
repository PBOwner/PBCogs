from redbot.core.bot import Red

from .autoconfigcleaner import AutoConfigCleaner

async def setup(bot: Red):
    await bot.add_cog(AutoConfigCleaner(bot))
