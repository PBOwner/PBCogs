import asyncio
from redbot.core.bot import Red

async def setup(bot: Red):
    from .ownerprotection import OwnerProtection

    # Create an instance of the OwnerProtection cog
    cog = OwnerProtection(bot)

    # Add the cog to the bot
    await bot.add_cog(cog)

    # Register the context menu commands
    bot.tree.add_command(cog.add_to_protected_owners_list)
    bot.tree.add_command(cog.remove_from_protected_owners_list)
