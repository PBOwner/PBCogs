from redbot.core.bot import Red

from .multicommands import MultiCommands

async def setup(bot: Red):
    await bot.add_cog(MultiCommands(bot))
