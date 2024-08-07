from redbot.core.bot import Red
from .ownerprotection import OwnerProtection

__red_end_user_data_statement__ = (
    "This cog does not store any end user data."
)

async def setup(bot: Red):
    cog = OwnerProtection(bot)
    await cog.cog_load()
    bot.add_cog(cog)
