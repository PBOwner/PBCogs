import asyncio
from redbot.core.bot import Red
from .ownerprotection import OwnerProtection, add_to_protected_owners_list, remove_from_protected_owners_list

async def setup(bot: Red):
    cog = OwnerProtection(bot)
    await bot.add_cog(cog)
    bot.tree.add_command(add_to_protected_owners_list)
    bot.tree.add_command(remove_from_protected_owners_list)
    await bot.tree.sync()
