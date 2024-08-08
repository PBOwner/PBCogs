from redbot.core.bot import Red
from .ownerprotection import (
    OwnerProtection,
    add_to_protected_owners_list,
    remove_from_protected_owners_list,
)

async def setup(bot: Red):
    cog = OwnerProtection(bot)
    bot.tree.add_command(add_to_protected_owners_list)
    bot.tree.add_command(remove_from_protected_owners_list)
