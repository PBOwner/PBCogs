import discord
from discord.ext import commands
from redbot.core import commands, Config
import requests

class URLShortener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_global = {
            "tinyurl_token": None,
            "custom_domain": "tiny.one"
        }
        self.config.register_global(**default_global)

    @commands.command()
    @commands.is_owner()
    async def settinyurltoken(self, ctx, token: str):
        """Set the TinyURL API token."""
        await self.config.tinyurl_token.set(token)
        await ctx.send("TinyURL API token has been set.")

    @commands.command()
    @commands.is_owner()
    async def setcustomdomain(self, ctx, domain: str):
        """Set the custom domain for shortened URLs."""
        await self.config.custom_domain.set(domain)
        await ctx.send(f"Custom domain has been set to: {domain}")

    @commands.command()
    async def vanity(self, ctx, custom_name: str, *, url: str):
        """Create a vanity URL with a custom name using TinyURL."""
        tinyurl_token = await self.config.tinyurl_token()
        custom_domain = await self.config.custom_domain()
        if not tinyurl_token:
            return await ctx.send("TinyURL API token is not set. Please set it using `!settinyurltoken` command.")

        headers = {
            "Authorization": f"Bearer {tinyurl_token}",
            "Content-Type": "application/json"
        }
        data = {
            "url": url,
            "domain": custom_domain,
            "alias": custom_name
        }

        response = requests.post("https://api.tinyurl.com/create", headers=headers, json=data)
        if response.status_code == 200:
            short_url = response.json()["data"]["tiny_url"]
            await ctx.send(f"Vanity URL created: {short_url}")
        else:
            await ctx.send(f"Failed to create vanity URL: {response.json().get('errors', 'Unknown error')}")
