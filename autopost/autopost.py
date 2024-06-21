import aiohttp
from redbot.core import commands, Config, checks
from discord.ext import tasks
import logging

log = logging.getLogger("red.autopost")

class AutoPost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567892)  # Unique identifier
        default_global = {
            "topgg_token": "",
            "dbl_token": "",
            "update_interval": 1800  # Default to 30 minutes
        }
        self.config.register_global(**default_global)
        self.session = aiohttp.ClientSession()
        self.update_stats.start()

    def cog_unload(self):
        self.update_stats.cancel()
        self.bot.loop.create_task(self.session.close())

    @commands.group(invoke_without_command=True)
    @checks.is_owner()
    async def autopost(self, ctx):
        """Group command for managing auto-posting to bot listing sites."""
        await ctx.send_help(ctx.command)

    @autopost.command(name="settopgg")
    async def set_topgg_token(self, ctx, token: str):
        """Set the top.gg API token.

        Example usage:
        [p]autopost settopgg <your_topgg_token>

        Replace <your_topgg_token> with the actual API token you obtained from top.gg.
        """
        await self.config.topgg_token.set(token)
        await ctx.send("top.gg token has been set.")
        log.info(f"top.gg token set by {ctx.author.name}")

    @autopost.command(name="setdbl")
    async def set_dbl_token(self, ctx, token: str):
        """Set the discordbotlist.com API token.

        Example usage:
        [p]autopost setdbl <your_dbl_token>

        Replace <your_dbl_token> with the actual API token you obtained from discordbotlist.com.
        """
        await self.config.dbl_token.set(token)
        await ctx.send("discordbotlist.com token has been set.")
        log.info(f"discordbotlist.com token set by {ctx.author.name}")

    @autopost.command(name="setinterval")
    async def set_update_interval(self, ctx, interval: int):
        """Set the update interval in seconds.

        Example usage:
        [p]autopost setinterval <interval_in_seconds>

        Replace <interval_in_seconds> with the desired interval in seconds.
        """
        await self.config.update_interval.set(interval)
        self.update_stats.change_interval(seconds=interval)
        await ctx.send(f"Update interval has been set to {interval} seconds.")
        log.info(f"Update interval set to {interval} seconds by {ctx.author.name}")

    @tasks.loop(seconds=1800)
    async def update_stats(self):
        await self.bot.wait_until_ready()
        guild_count = len(self.bot.guilds)
        topgg_token = await self.config.topgg_token()
        dbl_token = await self.config.dbl_token()

        headers_topgg = {"Authorization": topgg_token}
        headers_dbl = {"Authorization": dbl_token}

        if topgg_token:
            await self.post_to_topgg(guild_count, headers_topgg)
        if dbl_token:
            await self.post_to_dbl(guild_count, headers_dbl)

    async def post_to_topgg(self, guild_count, headers):
        url = f"https://top.gg/api/bots/{self.bot.user.id}/stats"
        payload = {"server_count": guild_count}
        async with self.session.post(url, json=payload, headers=headers) as response:
            if response.status == 200:
                log.info("Successfully posted stats to top.gg")
            else:
                log.error(f"Failed to post stats to top.gg: {response.status}")

    async def post_to_dbl(self, guild_count, headers):
        url = f"https://discordbotlist.com/api/v1/bots/{self.bot.user.id}/stats"
        payload = {"guilds": guild_count}
        async with self.session.post(url, json=payload, headers=headers) as response:
            if response.status == 200:
                log.info("Successfully posted stats to discordbotlist.com")
            else:
                log.error(f"Failed to post stats to discordbotlist.com: {response.status}")

def setup(bot):
    bot.add_cog(AutoPost(bot))
