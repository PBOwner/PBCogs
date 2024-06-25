from redbot.core.bot import Red

from .commandidea import CommandIdea

async def setup(bot: Red):
    await bot.add_cog(CommandIdea(bot))
