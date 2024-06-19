import discord
from redbot.core import commands
import random
import re

class NoFuckYou(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.fuck_you_gifs = [
            "https://media.giphy.com/media/l3vR6aasfsfsfsfsfs/giphy.gif",
            "https://media.giphy.com/media/3o6ZsW2F6zfsfsfsfs/giphy.gif",
            "https://media.giphy.com/media/26ufdipQqUfsfsfsf/giphy.gif",
            # Add more URLs to your list
        ]
        # Compile a regex pattern to match variations of "fuck you"
        self.pattern = re.compile(r'\b(f[aeiou]*c*k\s*y[aeiou]*u)\b', re.IGNORECASE)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if self.pattern.search(message.content):
            response = f"No, Fuck you {message.author.mention}!"
            try:
                await message.channel.send(response)
            except Exception as e:
                print(f"Failed to send message: {e}")
                print(f"Channel: {message.channel}, Message: {message.content}")

            random_gif = random.choice(self.fuck_you_gifs)
            try:
                await message.channel.send(random_gif)
            except Exception as e:
                print(f"Failed to send GIF: {e}")
                print(f"Channel: {message.channel}, Message: {message.content}")

def setup(bot):
    bot.add_cog(NoFuckYou(bot))
