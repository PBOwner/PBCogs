from redbot.core.bot import Red

from .userinstall import UserInstall

async def setup(bot: Red):
    await bot.add_cog(UserInstall(bot))
