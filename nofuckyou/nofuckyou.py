import discord
from redbot.core import commands
import random

class NoFuckYou(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.fuck_you_gifs = [
            "https://media.giphy.com/media/l3vR6aasfsfsfsfsfs/giphy.gif",
            "https://media.giphy.com/media/3o6ZsW2F6zfsfsfsfs/giphy.gif",
            "https://media.giphy.com/media/26ufdipQqUfsfsfsf/giphy.gif",
            # Add more URLs to your list
        ]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if "fuck you" in message.content.lower():
            response = f"No, Fuck you {message.author.mention}!"
            await message.channel.send(response)

            random_gif = random.choice(self.fuck_you_gifs)
            await message.channel.send(random_gif)

def setup(bot):
    bot.add_cog(NoFuckYou(bot))
