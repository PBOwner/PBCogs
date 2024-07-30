from redbot.core.bot import Red

from .slashrouterimport SlashRouter

async def setup(bot: Red):
    await bot.add_cog(SlashRouter(bot))
