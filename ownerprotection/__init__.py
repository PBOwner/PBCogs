from redbot.core.bot import Red
from .ownerprotection import (
    OwnerProtection,
    add_to_protected_owners_list,
    remove_from_protected_owners_list,
)

async def setup(bot: Red):
    cog = OwnerProtection(bot)
    await cog.cog_load()
    bot.add_cog(cog)
    bot.tree.add_command(add_to_protected_owners_list)
    bot.tree.add_command(remove_from_protected_owners_list)

async def teardown(bot: Red):
    bot.tree.remove_command("Add to Protected Owners", type=discord.AppCommandType.user)
    bot.tree.remove_command("Remove from Protected Owners", type=discord.AppCommandType.user)
