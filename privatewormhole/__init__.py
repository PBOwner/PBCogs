from redbot.core.bot import Red

from .privatewormhole import PrivateWormHole

async def setup(bot):
    await bot.add_cog(PrivateWormHole(bot))
