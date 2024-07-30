from redbot.core.bot import Red

from .slashrouter import SlashRouter

async def setup(bot: Red):
    await bot.add_cog(SlashRouter(bot))
