import discord
from redbot.core import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import requests

class QOTD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_job(self.post_question_of_the_day, 'cron', hour=6)  # Schedule the job to run daily at 12:00 AM
        self.scheduler.start()
        self.question_channel = None

    def get_random_question(self):
        if self.api_endpoint:
            response = requests.get(self.api_endpoint)
            if response.status_code == 200:
                question_data = response.json()
                question = question_data.get("question")
                return question
        return "No question available today. Check back tomorrow!"

    async def post_question_of_the_day(self):
        if self.question_channel:
            question = self.get_random_question()
            embed = discord.Embed(title="🌟 Question of the Day", description=question, color=0x00f0ff)
            await self.question_channel.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def setqotdtime(self, ctx, hour: int):
        self.scheduler.reschedule_job(self.post_question_of_the_day, trigger='cron', hour=hour)
        await ctx.send(f"Question of the Day posting time set to {hour}:00", delete_after=5)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def setqotdchannel(self, ctx, channel: discord.TextChannel):
        self.question_channel = channel
        await ctx.message.delete()
        await ctx.send(f"Question of the Day channel set to {channel.mention}", delete_after=5)

    @set_question_channel.error
    async def set_question_channel_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please mention a text channel to set as the question channel.", delete_after=5)

def setup(bot):
    bot.add_cog(QOTD(bot))
