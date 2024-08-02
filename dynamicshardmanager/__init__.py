from redbot.core.bot import Red

from .dynamicshardmanager import DynamicShardManager

async def setup(bot: Red):
    await bot.add_cog(DynamicShardManager(bot))
