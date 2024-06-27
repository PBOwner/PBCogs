import aiohttp
from bs4 import BeautifulSoup
from redbot.core import commands, Config

class GoogleSearch(commands.Cog):
    """Google Search cog"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_global = {
            "api_key": "",
            "cse_id": ""
        }
        self.config.register_global(**default_global)

    @commands.command()
    async def setapikey(self, ctx, api_key: str):
        """Sets the Google API key."""
        await self.config.api_key.set(api_key)
        await ctx.send("Google API key set successfully.")

    @commands.command()
    async def setcseid(self, ctx, cse_id: str):
        """Sets the Google Custom Search Engine ID."""
        await self.config.cse_id.set(cse_id)
        await ctx.send("Google Custom Search Engine ID set successfully.")

    @commands.command()
    async def google(self, ctx, *, query: str):
        """Searches Google and returns the most relevant site and its content."""
        api_key = await self.config.api_key()
        cse_id = await self.config.cse_id()

        if not api_key or not cse_id:
            await ctx.send("API key or Custom Search Engine ID is not set. Use `!setapikey` and `!setcseid` to set them.")
            return

        search_url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={api_key}&cx={cse_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(search_url) as response:
                if response.status != 200:
                    await ctx.send("Failed to fetch search results.")
                    return

                data = await response.json()
                if "items" in data:
                    top_result = data["items"][0]
                    title = top_result["title"]
                    link = top_result["link"]

                    # Fetch the content of the site
                    async with session.get(link) as site_response:
                        if site_response.status != 200:
                            await ctx.send(f"Failed to fetch content from {link}.")
                            return

                        site_content = await site_response.text()
                        soup = BeautifulSoup(site_content, 'html.parser')
                        # Extract text content from the site
                        text_content = soup.get_text(separator='\n', strip=True)
                        # Limit the content to the first 2000 characters to avoid exceeding Discord's message limit
                        text_content = text_content[:2000]

                        await ctx.send(f"**{title}**\n{link}\n\n{text_content}")
                else:
                    await ctx.send("No results found.")
