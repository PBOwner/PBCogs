from redbot.core.bot import Red
from .voice_channel_manager import VoiceChannelManager

async def setup(bot):
    bot.add_cog(VoiceChannelManager(bot))
