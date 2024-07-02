from redbot.core.bot import Red

from .featurerequest import FeatureRequest
from .featurerequest import SlashRequest

async def setup(bot: Red):
    await bot.add_cog(FeatureRequest(bot))
    await bot.add_cog(SlashRequest(bot))
