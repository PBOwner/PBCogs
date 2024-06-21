import aiohttp
from redbot.core import commands

class Roast(commands.Cog):
    """Cog for roasting users using a public API."""

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    @commands.command()
    async def roast(self, ctx, user: commands.MemberConverter = None):
        """Roast a user or yourself if no user is mentioned."""
        if user is None:
            user = ctx.author

        roast = await self.get_roast()
        if roast:
            await ctx.send(f"{user.mention}, {roast}")
        else:
            await ctx.send("Couldn't fetch a roast at the moment. Try again later.")

    async def get_roast(self):
        """Fetch a roast from a public API."""
        url = "https://evilinsult.com/generate_insult.php?lang=en&type=json"

        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("insult")
            else:
                return None

def setup(bot):
    bot.add_cog(Roast(bot))
