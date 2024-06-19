from redbot.core.bot import Red

from .nofuckyou import NoFuckYou

async def setup(bot):
    await bot.add_cog(NoFuckYou(bot))
