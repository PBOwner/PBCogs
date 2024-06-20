from redbot.core.bot import Red

from .msgreport import MsgReport

async def setup(bot):
    await bot.add_cog(MsgReport(bot))
