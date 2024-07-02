from redbot.core.bot import Red

from .featurerequest import FeatureRequest

async def setup(bot):
    await bot.add_cog(FeatureRequest(bot))
    await bot.add_cog(SlashRequest(bot))
