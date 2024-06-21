from redbot.core.bot import Red

from .autopost import AutoPost

async def setup(bot):
    await bot.add_cog(AutoPost(bot))
