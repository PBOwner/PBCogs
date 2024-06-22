from redbot.core.bot import Red

from .counter import Counter

async def setup(bot: Red):
    await bot.add_cog(Counter(bot))
