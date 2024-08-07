from redbot.core.bot import Red
from .adwarn import AdWarn

async def setup(bot):
    cog = AdWarn(bot)
    await bot.add_cog(cog)
    bot.tree.add_command(adwarn_context_menu)
