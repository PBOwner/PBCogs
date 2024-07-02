import random
import uuid
import aiohttp
from redbot.core import commands
from redbot.core.bot import Red
import discord

class NSFWBDSM(commands.Cog):
    """NSFW BDSM cog for Red-DiscordBot"""

    def __init__(self, bot: Red):
        self.bot = bot
        self.giphy_api_key = "YOUR_GIPHY_API_KEY"
        self.tenor_api_key = "YOUR_TENOR_API_KEY"
        self.bdsms = {
            "aftercare": {
                "description": "A is for Aftercare"
            },
            "bondage": {
                "description": "B is for Bondage"
            },
            "cuckold": {
                "description": "C is for Cuckold"
            },
            "ds": {
                "description": "D is for D/S\nD/S refers to dominance and submission"
            },
            "edgeplay": {
                "description": "E is for Edgeplay"
            },
            "finishplay": {
                "description": "F is for Finishplay"
            },
            "hardlimits": {
                "description": "H is for Hard Limits"
            },
            "impactplay": {
                "description": "I is for Impact Play"
            },
            "japanesebondage": {
                "description": "J is for Japanese Bondage\nThe most well-known type of Japanese bondage is Shibari, in which one partner ties up the other in beautiful and intricate patterns using rope. It's a method of restraint, but also an art form."
            },
            "knifeplay": {
                "description": "K is for Knife Play"
            },
            "leather": {
                "description": "L is for Leather"
            },
            "masochist": {
                "description": "M is for Masochist"
            },
            "needleplay": {
                "description": "N is for Needle Play"
            },
            "orgasmdenial": {
                "description": "O is for Orgasm Denial"
            },
            "painslut": {
                "description": "P is for Painslut"
            },
            "queening": {
                "description": "Q is for Queening"
            },
            "rack": {
                "description": "R is for RACK\nRACK stands for Risk Aware Consensual Kink"
            },
            "switch": {
                "description": "S is for Switch"
            },
            "toppingfromthebottom": {
                "description": "T is for Topping From The Bottom"
            },
            "voyeurism": {
                "description": "V is for Voyeurism"
            },
            "wartenbergwheel": {
                "description": "W is for Wartenberg Wheel"
            },
            "yes": {
                "description": "Y is for Yes!\nBDSM is all about enthusiastic consent. The dominant partner won't step on their submissive's head and then shove it into a toilet without a big ole 'yes, please!'"
            },
            "zentai": {
                "description": "Z is for Zentai\nZentai is a skintight Japanese body suit typically made of spandex and nylon"
            }
        }

    async def fetch_gif_url(self, query):
        try:
            service = random.choice(['giphy', 'tenor'])
            if service == 'giphy':
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"https://api.giphy.com/v1/gifs/search?api_key={self.giphy_api_key}&q={query}&limit=1&offset={random.randint(0, 50)}&rating=R") as response:
                        data = await response.json()
                        return data['data'][0]['images']['original']['url']
            else:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"https://api.tenor.com/v1/search?q={query}&key={self.tenor_api_key}&limit=1&pos={random.randint(0, 50)}&contentfilter=high") as response:
                        data = await response.json()
                        return data['results'][0]['media'][0]['gif']['url']
        except Exception as e:
            print(f"Error fetching GIF: {e}")
            return "https://example.com/default.gif"  # Fallback GIF URL

    async def send_embed(self, ctx, target, title, description, gif_url):
        embed = discord.Embed(title=title, description=description, color=discord.Color.dark_red())
        embed.set_image(url=gif_url)
        await ctx.send(embed=embed)

        if not ctx.guild.get_member(target.id):
            try:
                await target.send(embed=embed)
            except discord.Forbidden:
                await ctx.send(f"Could not send a DM to {target.display_name}.")

    @commands.group(invoke_without_command=True)
    @commands.is_nsfw()
    async def nsfw(self, ctx, target: discord.Member = None, *, custom_message: str = None):
        """NSFW BDSM commands."""
        if target is None and custom_message is None:
            await ctx.send("Please mention a user or provide a custom message.")
            return

        gif_url = await self.fetch_gif_url("bdsm")
        await self.send_embed(ctx, target, f"NSFW for {target.display_name}", custom_message, gif_url)

    @nsfw.command()
    @commands.is_nsfw()
    async def bdsm(self, ctx, kink: str, target: discord.Member, *, custom_message: str = None):
        """Send a BDSM command to a user with a default or custom NSFW message."""
        if kink not in self.bdsms:
            await ctx.send("Invalid kink. Please choose a valid kink.")
            return

        description = custom_message if custom_message else self.bdsms[kink]["description"]
        gif_url = await self.fetch_gif_url(kink)
        await self.send_embed(ctx, target, f"NSFW {kink.capitalize()} for {target.display_name}", description, gif_url)

    @nsfw.command()
    @commands.is_nsfw()
    async def add(self, ctx, kink: str, *, new_message: str):
        """Add a new NSFW message to a kink."""
        if kink not in self.bdsms:
            await ctx.send("Invalid kink. Please choose a valid kink.")
            return

        message_id = str(uuid.uuid4())
        self.bdsms[kink][message_id] = new_message
        await ctx.send(f"Added new message to {kink} with ID {message_id}: {new_message}")

    @nsfw.command()
    @commands.is_nsfw()
    async def remove(self, ctx, kink: str, message_id: str):
        """Remove an NSFW message by its UUID from a kink."""
        if kink not in self.bdsms:
            await ctx.send("Invalid kink. Please choose a valid kink.")
            return

        if message_id in self.bdsms[kink]:
            removed_message = self.bdsms[kink].pop(message_id)
            await ctx.send(f"Removed message from {kink} with ID {message_id}: {removed_message}")
        else:
            await ctx.send(f"No message found with ID {message_id} in {kink}")

    @nsfw.command()
    @commands.is_nsfw()
    async def list(self, ctx, kink: str = None):
        """List all NSFW messages in a kink."""
        if kink is not None and kink not in self.bdsms:
            await ctx.send("Invalid kink. Please choose a valid kink.")
            return

        if kink:
            messages = self.bdsms[kink]
            if not messages:
                await ctx.send(f"No messages available in {kink}.")
                return

            pages = []
            current_page = 0
            page_limit = 5  # Number of messages per page
            messages_list = list(messages.items())

            while current_page * page_limit < len(messages_list):
                embed = discord.Embed(title=f"{kink.capitalize()} Messages (Page {current_page + 1})", color=discord.Color.dark_red())
                for i in range(page_limit):
                    if current_page * page_limit + i >= len(messages_list):
                        break
                    message_id, message = messages_list[current_page * page_limit + i]
                    embed.add_field(
                        name=f"Message ID: {message_id}",
                        value=message,
                        inline=False
                    )
                pages.append(embed)
                current_page += 1

            for page in pages:
                await ctx.send(embed=page)
        else:
            for kink, messages in self.bdsms.items():
                if not messages:
                    await ctx.send(f"No messages available in {kink}.")
                    continue

                pages = []
                current_page = 0
                page_limit = 5  # Number of messages per page
                messages_list = list(messages.items())

                while current_page * page_limit < len(messages_list):
                    embed = discord.Embed(title=f"{kink.capitalize()} Messages (Page {current_page + 1})", color=discord.Color.dark_red())
                    for i in range(page_limit):
                        if current_page * page_limit + i >= len(messages_list):
                            break
                        message_id, message = messages_list[current_page * page_limit + i]
                        embed.add_field(
                            name=f"Message ID: {message_id}",
                            value=message,
                            inline=False
                        )
                    pages.append(embed)
                    current_page += 1

                for page in pages:
                    await ctx.send(embed=page)
