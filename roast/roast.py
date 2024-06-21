import aiohttp
import random
from redbot.core import commands
import discord

class Roast(commands.Cog):
    """Cog for delivering roasts using a combination of predefined messages and a public API."""

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.predefined_roasts = [
            "You're as useless as the 'ueue' in 'queue'.",
            "If I had a dollar for every time you said something smart, I'd be broke.",
            "You're not stupid; you just have bad luck thinking.",
            "You're proof that even god makes mistakes sometimes.",
            "I'd agree with you, but then we'd both be wrong.",
            "You bring everyone so much joy when you leave the room.",
            "You're like a cloud. When you disappear, it's a beautiful day.",
            "You're the reason why they put instructions on shampoo.",
            "Your secrets are always safe with me. I never even listen when you tell me them.",
            "I'd explain it to you, but I left my crayons at home."
        ]

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    @commands.command()
    async def roast(self, ctx, user: discord.User = None):
        """Deliver a roast to a user or yourself if no user is mentioned or provided."""
        if user is None:
            user = ctx.author

        roast = await self.get_roast()
        if roast:
            await ctx.send(f"{user.mention}, {roast}")
        else:
            await ctx.send("Couldn't fetch a roast at the moment. Try again later.")

    async def get_roast(self):
        """Fetch a roast from a predefined list or a public API."""
        if random.choice([True, False]):
            return random.choice(self.predefined_roasts)
        else:
            return await self.fetch_roast_from_api()

    async def fetch_roast_from_api(self):
        """Fetch a roast from the evilinsult.com API."""
        url = "https://evilinsult.com/generate_insult.php?lang=en&type=json"

        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("insult")
            else:
                return None

def setup(bot):
    bot.add_cog(Roast(bot))
