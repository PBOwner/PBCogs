from redbot.core.bot import Red
from .adwarn import AdWarn, adwarn_context_menu

async def setup(bot: Red):
    cog = AdWarn(bot)
    await bot.add_cog(cog)
    bot.tree.add_command(adwarn_context_menu)

async def teardown(bot: Red):
    bot.tree.remove_command("AdWarn", type=discord.AppCommandType.user)
