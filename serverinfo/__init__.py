from redbot.core.bot import Red

from .serverinfo import ServerInfo

async def setup(bot):
    await bot.add_cog(ServerInfo(bot))
