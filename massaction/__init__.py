from redbot.core.bot import Red

from .massaction import MassAction

async def setup(bot: Red):
    await bot.add_cog(MassAction(bot))
