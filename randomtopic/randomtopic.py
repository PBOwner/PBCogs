import discord
import aiohttp
import asyncio
import random
from redbot.core import commands, Config, checks
from redbot.core.bot import Red

class RandomTopic(commands.Cog):
    """A cog to send random topics at configurable intervals."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_guild(
            channel_id=None,
            role_id=None,
            embed_title="Random Topic",
            interval=60  # Default interval in minutes
        )
        self.session = aiohttp.ClientSession()
        self.tasks = {}

    def cog_unload(self):
        asyncio.create_task(self.session.close())
        for task in self.tasks.values():
            task.cancel()

    @commands.group()
    @commands.guild_only()
    @checks.admin_or_permissions(manage_guild=True)
    async def rt(self, ctx):
        """Commands to configure Random Topic."""
        pass

    @rt.command()
    async def setchannel(self, ctx, channel: discord.TextChannel):
        """Set the channel where random topics will be sent.

        Use this command to specify which text channel the bot should use to send the random topics. Make sure to mention the channel.
        """
        await self.config.guild(ctx.guild).channel_id.set(channel.id)
        await ctx.send(f"Channel set to {channel.name}")

    @rt.command()
    async def setrole(self, ctx, role: discord.Role):
        """Set the role to be pinged when a new topic is posted.

        Use this command to specify which role should be mentioned whenever a new random topic is generated and sent to the channel.
        """
        await self.config.guild(ctx.guild).role_id.set(role.id)
        await ctx.send(f"Role set to {role.name}", allowed_mentions=discord.AllowedMentions(roles=True))

    @rt.command()
    async def settitle(self, ctx, *, title: str):
        """Set the title for the Random Topic embed.

        Use this command to customize the title that will appear in the random topic embeds.
        """
        await self.config.guild(ctx.guild).embed_title.set(title)
        await ctx.send(f"Embed title set to {title}")

    @rt.command()
    async def setinterval(self, ctx, interval: int):
        """Set the interval for sending random topics (in minutes).

        Use this command to set the interval at which the bot will send random topics.
        """
        await self.config.guild(ctx.guild).interval.set(interval)
        await ctx.send(f"Interval set to {interval} minutes")
        await self.restart_task(ctx.guild.id)

    async def send_random_topic(self, guild: discord.Guild):
        role_id = await self.config.guild(guild).role_id()
        channel_id = await self.config.guild(guild).channel_id()
        embed_title = await self.config.guild(guild).embed_title()

        if channel_id is None:
            return

        channel = guild.get_channel(channel_id)
        if channel is None:
            return

        try:
            async with self.session.get("https://the-trivia-api.com/api/questions?limit=1") as resp:
                if resp.status != 200:
                    await channel.send("Failed to retrieve a random topic. Please try again later.")
                    return
                data = await resp.json()
                question_data = data[0]
                question = question_data['question']
                choices = question_data.get('incorrectAnswers', []) + [question_data['correctAnswer']]
                random.shuffle(choices)
        except aiohttp.ClientError:
            await channel.send("There was an error connecting to the random topic service. Please try again later.")
            return

        role_mention = f"<@&{role_id}>" if role_id else ""

        embed = discord.Embed(
            title=embed_title,
            color=random.randint(0, 0xFFFFFF)
        )
        embed.add_field(name="Question", value=question, inline=False)

        if choices:
            for i, choice in enumerate(choices, 1):
                embed.add_field(name=f"Choice {i}", value=choice, inline=True)

        try:
            if role_mention:
                await channel.send(role_mention, allowed_mentions=discord.AllowedMentions(roles=True))
            await channel.send(embed=embed)
        except discord.HTTPException:
            await channel.send("Failed to send the random topic. Please try again later.")

    async def scheduled_task(self, guild_id):
        await self.bot.wait_until_ready()
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return

        while True:
            await self.send_random_topic(guild)
            interval = await self.config.guild(guild).interval()
            await asyncio.sleep(interval * 60)

    async def restart_task(self, guild_id):
        if guild_id in self.tasks:
            self.tasks[guild_id].cancel()
        self.tasks[guild_id] = self.bot.loop.create_task(self.scheduled_task(guild_id))

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            self.tasks[guild.id] = self.bot.loop.create_task(self.scheduled_task(guild.id))
