import discord
from redbot.core import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import requests

class QOTD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_job(self.post_question_of_the_day, 'cron', hour=6)  # Schedule the job to run daily at 6:00 AM
        self.scheduler.start()
        self.question_channel = None
        self.api_endpoint = "https://api.example.com/questions"  # Replace with your actual API endpoint

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
            embed = discord.Embed(title="Question of the Day", color=0x00f0ff)
            embed.add_field(name="Question", value=question)
            embed.add_field(name="Answer this question in the attached field!", value="Join the thread to share your answer!")
            message = await self.question_channel.send(embed=embed)
            await message.create_thread(name="QOTD Answers", message="Welcome to the thread for answering today's Question of the Day!")

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

    @setqotdchannel.error
    async def setqotdchannel_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please mention a text channel to set as the question channel.", delete_after=5)

def setup(bot):
    bot.add_cog(QOTD(bot))
