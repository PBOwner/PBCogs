from redbot.core.bot import Red

from .bumper import Bumper

async def setup(bot: Red):
    await bot.add_cog(Bumper(bot))
