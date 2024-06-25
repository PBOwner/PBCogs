import aiohttp
from redbot.core import commands

class CommandIdeas(commands.Cog):
    """Cog to fetch random command ideas from an online source"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def commandidea(self, ctx):
        """Get a random command idea from an online source"""
        url = "https://www.boredapi.com/api/activity"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    idea = data.get("activity", "No idea found.")
                    await ctx.send(f"Here's a random command idea: {idea}")
                else:
                    await ctx.send("Failed to fetch a command idea. Please try again later.")
