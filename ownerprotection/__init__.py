from redbot.core.bot import Red

from .ownerprotection import OwnerProtection

async def setup(bot):
    """Setup the OwnerProtection cog."""
    await bot.add_cog(OwnerProtection(bot))
