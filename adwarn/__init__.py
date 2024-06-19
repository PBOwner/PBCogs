from redbot.core.bot import Red

from .adwarn import AdWarn

async def setup(bot):
    await bot.add_cog(NoFuckYou(bot))
