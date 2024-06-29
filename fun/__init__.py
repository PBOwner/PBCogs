from redbot.core.bot import Red

from .fun import Fun

async def setup(bot: Red):
    await bot.add_cog(Fun(bot))
