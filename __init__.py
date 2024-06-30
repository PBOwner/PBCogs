from redbot.core.bot import Red

from .rolemembers import RoleMembers

async def setup(bot: Red):
    await bot.add_cog(RoleMembers(bot))
