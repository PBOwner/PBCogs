from redbot.core.bot import Red

from .rendemoji import RandomEmoji

async def setup(bot):
    await bot.add_cog(RandomEmoji(bot))
