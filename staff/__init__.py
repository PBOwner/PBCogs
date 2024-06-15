from redbot.core.bot import Red

from .staff import StaffManager

async def setup(bot):
    await bot.add_cog(StaffManager(bot))
