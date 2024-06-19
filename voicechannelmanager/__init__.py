from redbot.core.bot import Red
from .voicechannelmanager import VoiceChannelManager

async def setup(bot):
    bot.add_cog(VoiceChannelManager(bot))
