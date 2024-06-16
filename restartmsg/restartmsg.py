import os
from redbot.core import commands

class RestartMsg(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='warnrestart')
    @commands.is_owner()
    async def warnrestart(self, ctx, *, message: str):
        """Send a message to all Server Owners."""
        for guild in self.bot.guilds:
            owner = guild.owner
            try:
                await owner.send(message)
            except Exception as e:
                print(f"Failed to send message to {owner}: {e}")

        await ctx.send("Restart message sent to all guild owners. Restarting bot...")

        # Restart the bot process
        os.execv(sys.executable, ['python'] + sys.argv)

def setup(bot):
    bot.add_cog(RestartMsg(bot))
