from redbot.core.bot import Red

from .hybridcommands import HybridCommands

async def setup(bot: Red):
    await bot.add_cog(HybridCommands(bot))
