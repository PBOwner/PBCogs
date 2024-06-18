import discord
from redbot.core import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import requests

class QOTD(commands.Cog):
    """
    A cog that posts a random question of the day to a designated channel.
    """

    def __init__(self, bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_job(self.post_question_of_the_day, 'cron', hour=6)  # Schedule the job to run daily at 6:00 AM
        self.scheduler.start()
        self.question_channels = {}  # Dictionary to store question channels per server
        self.api_endpoint = "https://quizapi.io/api/v1/questions"  # QuizAPI endpoint
        self.api_key = None

    def get_random_question(self):
        """
        Fetches a random question from the QuizAPI.

        Returns:
            str: The question text, or an error message if no question is available.
        """
        if self.api_key and self.api_endpoint:
            headers = {"Authorization": f"Token {self.api_key}"}
            response = requests.get(self.api_endpoint, headers=headers)
            if response.status_code == 200:
                question_data = response.json()
                question = question_data[0].get("question")  # Assuming the API returns a list of questions
                return question
        return "No question available today. Check back tomorrow!"

    async def post_question_of_the_day(self):
        """
        Posts the question of the day to the designated channel.
        """
        for guild_id, channel in self.question_channels.items():
            if channel:
                try:
                    question = self.get_random_question()
                    if question:
                        embed = discord.Embed(title="Question of the Day", color=0x00f0ff)
                        embed.add_field(name="Question", value=question)
                        embed.add_field(name="Answer this question in the attached field!", value="Join the thread to share your answer!")
                        message = await channel.send(embed=embed)  # Ensure channel is a discord.TextChannel
                        await message.create_thread(name="QOTD Answers", content="Welcome to the thread for answering today's Question of the Day!")
                except AttributeError as e:
                    print(f"Error sending message to channel: {e}")
            else:
                print(f"No valid channel set for guild ID {guild_id}.")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def setqotdtime(self, ctx, hour: int):
        """
        Sets the time of day when the question of the day is posted.

        Args:
            ctx (commands.Context): The context of the command.
            hour (int): The hour (0-23) to post the question.
        """
        self.scheduler.reschedule_job(self.post_question_of_the_day, trigger='cron', hour=hour)
        await ctx.send(f"Question of the Day posting time set to {hour}:00", delete_after=5)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def setqotdchannel(self, ctx, channel: discord.TextChannel):
        """
        Sets the channel where the question of the day is posted.

        Args:
            ctx (commands.Context): The context of the command.
            channel (discord.TextChannel): The channel to post the question to.
        """
        self.question_channels[ctx.guild.id] = channel
        await ctx.message.delete()
        await ctx.send(f"Question of the Day channel set to {channel.mention}", delete_after=5)

    @setqotdchannel.error
    async def setqotdchannel_error(self, ctx, error):
        """
        Handles errors when setting the question channel.

        Args:
            ctx (commands.Context): The context of the command.
            error (Exception): The error that occurred.
        """
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please mention a text channel to set as the question channel.", delete_after=5)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def setqotdapi(self, ctx, api_key: str):
        """
        Sets the API key for the QuizAPI.

        Args:
            ctx (commands.Context): The context of the command.
            api_key (str): The API key to use.
        """
        self.api_key = api_key
        await ctx.message.delete()
        await ctx.send("API key set successfully.", delete_after=5)

def setup(bot):
    """
    Adds the cog to the bot.

    Args:
        bot (discord.Bot): The bot instance.
    """
    bot.add_cog(QOTD(bot))
