from redbot.core.bot import Red

from .dynamicformcog import DynamicFormCog

async def setup(bot):
    await bot.add_cog(DynamicFormCog(bot))
