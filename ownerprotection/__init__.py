import asyncio
from redbot.core.bot import Red
from .ownerprotection import OwnerProtection

async def setup(bot: Red):
    cog = OwnerProtection(bot)
    await bot.add_cog(cog)
