from redbot.core import commands

class RestartMsg(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='warnrestart')
    @commands.is_owner()
    async def warnrestart(self, ctx, *, message: str):
        for guild in self.bot.guilds:
            owner = guild.owner
            try:
                await owner.send(message)
            except Exception as e:
                print(f"Failed to send message to {owner}: {e}")

        await ctx.send("Restart message sent to all guild owners.")

def setup(bot):
    bot.add_cog(RestartMsg(bot))
