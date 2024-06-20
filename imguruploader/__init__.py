from redbot.core.bot import Red

from .imguruploader import ImgurUploader

async def setup(bot):
    await bot.add_cog(ImgurUploader(bot))
