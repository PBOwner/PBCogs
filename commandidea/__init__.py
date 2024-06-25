from redbot.core.bot import Red

from .commandidea import CommandIdeas

async def setup(bot: Red):
    await bot.add_cog(CommandIdeas(bot))
