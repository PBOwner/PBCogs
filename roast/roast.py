import aiohttp
import random
from redbot.core import commands, Config
import discord
import openai

class Roast(commands.Cog):
    """Cog for delivering roasts using a combination of predefined messages and OpenAI API."""

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_global(api_key=None)
        self.predefined_roasts = [
            "You're as useless as the 'ueue' in 'queue'.",
            "If I had a dollar for every time you said something smart, I'd be broke.",
            "You're not stupid; you just have bad luck thinking.",
            "You're proof that even god makes mistakes sometimes.",
            "I'd agree with you, but then we'd both be wrong.",
            "You bring everyone so much joy when you leave the room.",
            "You're like a cloud. When you disappear, it's a beautiful day.",
            "You're the reason why they put instructions on shampoo.",
            "Your secrets are always safe with me. I never even listen when you tell me them.",
            "I'd explain it to you, but I left my crayons at home."
        ]

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    @commands.command()
    async def roast(self, ctx, user: discord.User = None):
        """Deliver a roast to a user or yourself if no user is mentioned or provided."""
        if user is None:
            user = ctx.author

        api_key = await self.config.api_key()
        if not api_key:
            await ctx.send("OpenAI API key is not set. Please set it using the `setapikey` command.")
            return

        openai.api_key = api_key

        # Fetch the last 50 messages from the user
        messages = await self.fetch_user_messages(ctx, user, limit=50)
        if not messages:
            await ctx.send(f"Couldn't fetch messages for {user.mention}.")
            return

        # Generate a roast using OpenAI
        roast = await self.generate_roast(messages)
        if roast:
            await ctx.send(f"{user.mention}, {roast}")
        else:
            await ctx.send("Couldn't generate a roast at the moment. Try again later.")

    @commands.command()
    @commands.is_owner()
    async def openaiapi(self, ctx, key: str):
        """Set the OpenAI API key. This command is owner-only for security reasons."""
        await self.config.api_key.set(key)
        await ctx.message.delete()
        await ctx.send("API key has been set.", delete_after=5)

    async def fetch_user_messages(self, ctx, user: discord.User, limit: int = 50):
        """Fetch the last `limit` messages from the specified user in the context channel."""
        messages = []
        async for message in ctx.channel.history(limit=200):
            if message.author == user:
                messages.append(message.content)
                if len(messages) >= limit:
                    break
        return messages

    async def generate_roast(self, messages):
        """Generate a roast using OpenAI based on the provided messages."""
        prompt = (
            "Given the following messages, generate a humorous and light-hearted roast:\n\n"
            + "\n".join(messages) + "\n\nRoast:"
        )
        try:
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=prompt,
                max_tokens=60,
                n=1,
                stop=None,
                temperature=0.7,
            )
            return response.choices[0].text.strip()
        except Exception as e:
            print(f"Error generating roast: {e}")
            return None
