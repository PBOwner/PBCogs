from redbot.core.bot import Red

from .rendmoji import RandomEmoji

async def setup(bot):
    await bot.add_cog(RandomEmoji(bot))
