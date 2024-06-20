from redbot.core.bot import Red

from .requestgb import RequestGB

async def setup(bot):
    await bot.add_cog(RequestGB(bot))
