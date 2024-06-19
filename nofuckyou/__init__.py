from redbot.core.bot import Red

from .nofuckyou import NoFuckYou

def setup(bot):
    bot.add_cog(NoFuckYou(bot))
