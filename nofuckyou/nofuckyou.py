import discord
from redbot.core import commands, Config
import aiohttp
import random
import re

class NoFuckYou(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)  # Replace with a unique identifier
        self.config.register_global(giphy_api_key=None)
        self.pattern = re.compile(r'\b(f[aeiou]*c*k\s*y[aeiou]*u)\b', re.IGNORECASE)

    async def fetch_gif(self, query):
        giphy_api_key = await self.config.giphy_api_key()
        if not giphy_api_key:
            return None

        url = f"https://api.giphy.com/v1/gifs/search?api_key={giphy_api_key}&q={query}&limit=10&offset=0&rating=G&lang=en"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['data']:
                        return random.choice(data['data'])['images']['original']['url']
                return None

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if self.pattern.search(message.content):
            response = f"No, Fuck you {message.author.mention}!"
            try:
                if message.channel:
                    await message.channel.send(response)
                else:
                    print(f"Channel is None for message: {message.content} by {message.author} in {message.guild}")
            except Exception as e:
                print(f"Failed to send message: {e}")
                print(f"Channel: {message.channel}, Message: {message.content}")

            gif_url = await self.fetch_gif("fuck you")
            if gif_url:
                try:
                    if message.channel:
                        await message.channel.send(gif_url)
                    else:
                        print(f"Channel is None for message: {message.content} by {message.author} in {message.guild}")
                except Exception as e:
                    print(f"Failed to send GIF: {e}")
                    print(f"Channel: {message.channel}, Message: {message.content}")

    @commands.group()
    @commands.is_owner()
    async def giphy(self, ctx):
        """Group command for Giphy API key management."""
        pass

    @giphy.command()
    async def setkey(self, ctx, api_key: str):
        """Set the Giphy API key."""
        await self.config.giphy_api_key.set(api_key)
        await ctx.send("Giphy API key has been set.")

    @giphy.command()
    async def showkey(self, ctx):
        """Show the current Giphy API key."""
        api_key = await self.config.giphy_api_key()
        if api_key:
            await ctx.send(f"The current Giphy API key is: `{api_key}`")
        else:
            await ctx.send("No Giphy API key has been set.")

def setup(bot):
    bot.add_cog(NoFuckYou(bot))
