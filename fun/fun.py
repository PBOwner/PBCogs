import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
import random

class Fun(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot

    @commands.command(name='8ball')
    async def eightball(self, ctx, *, question: str):
        """Ask the magic 8-ball a question."""
        responses = [
            "It is certain.",
            "It is decidedly so.",
            "Without a doubt.",
            "Yes – definitely.",
            "You may rely on it.",
            "As I see it, yes.",
            "Most likely.",
            "Outlook good.",
            "Yes.",
            "Signs point to yes.",
            "Reply hazy, try again.",
            "Ask again later.",
            "Better not tell you now.",
            "Cannot predict now.",
            "Concentrate and ask again.",
            "Don't count on it.",
            "My reply is no.",
            "My sources say no.",
            "Outlook not so good.",
            "Very doubtful."
        ]
        response = random.choice(responses)
        await ctx.send(f"🎱 {response}")

    @commands.command()
    async def mock(self, ctx, *, text: str):
        """Mock a given text."""
        mocked_text = ''.join(random.choice([char.upper(), char.lower()]) for char in text)
        await ctx.send(mocked_text)

    @commands.command()
    async def memeify(self, ctx, *, text: str):
        """Memeify a given text."""
        memeified_text = ' '.join([char.upper() if i % 2 == 0 else char.lower() for i, char in enumerate(text)])
        await ctx.send(memeified_text)
