from redbot.core.bot import Red

from .invitesettings import InviteSettings

async def setup(bot):
    await bot.add_cog(InviteSettings(bot))
