from redbot.core.bot import Red

from .staffmanager import StaffManager

async def setup(bot):
    await bot.add_cog(StaffManager(bot))
