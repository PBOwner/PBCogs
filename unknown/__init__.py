from redbot.core.bot import Red

from .unknown import Unknown

async def setup(bot: Red):
    await bot.add_cog(Unknown(bot))
