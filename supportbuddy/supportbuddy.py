import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
from asyncio import TimeoutError
import requests
from bs4 import BeautifulSoup

class SupportBuddy(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "buddy_pending_requests": {},
            "buddy_questions": [
                "What is your name?",
                "What is your age?",
                "What are you seeking support for?"
            ],
            "requests_channel": None,
            "reaction_message_id": None,
            "reaction_emoji": "👍"
        }
        self.config.register_guild(**default_guild)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Handle reactions to the specified message."""
        if payload.user_id == self.bot.user.id:
            return  # Ignore reactions from the bot itself

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        user = guild.get_member(payload.user_id)
        if user.bot:
            return  # Ignore reactions from other bots

        reaction_message_id = await self.config.guild(guild).reaction_message_id()
        reaction_emoji = await self.config.guild(guild).reaction_emoji()
        if payload.message_id != reaction_message_id:
            return  # Ignore reactions to other messages

        # Remove the user's reaction
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        await message.remove_reaction(payload.emoji, user)

        if str(payload.emoji) != reaction_emoji:
            return  # Ignore reactions that are not the configured emoji

        # Send the questions to the user
        questions = await self.config.guild(guild).buddy_questions()
        if not questions:
            await user.send("No questions set for the support request.")
            return

        await user.send("Starting your request for a support buddy. Please answer the following questions:")

        responses = {}
        for question in questions:
            await user.send(f"Question: {question}")
            try:
                response = await self.bot.wait_for(
                    "message",
                    check=lambda m: m.author == user and isinstance(m.channel, discord.DMChannel),
                    timeout=300
                )
                responses[question] = response.content
            except TimeoutError:
                await user.send("You took too long to respond. Please try again later.")
                return

        async with self.config.guild(guild).buddy_pending_requests() as buddy_pending_requests:
            buddy_pending_requests[str(user.id)] = responses

        requests_channel_id = await self.config.guild(guild).requests_channel()
        requests_channel = self.bot.get_channel(requests_channel_id)

        if requests_channel:
            embed = discord.Embed(title=f"New Support Request - {user.display_name}", color=discord.Color.blue())
            for question, response in responses.items():
                embed.add_field(name=f"Question: {question}", value=f"Response: {response}", inline=False)
            await requests_channel.send(embed=embed)
            await user.send("Your request has been submitted. A moderator will pair you with a support buddy soon.")
        else:
            await user.send("Requests channel not set. Please contact an admin.")

    @commands.guild_only()
    @commands.command()
    async def buddyreq(self, ctx):
        """Request a support buddy."""
        questions = await self.config.guild(ctx.guild).buddy_questions()
        if not questions:
            await ctx.send("No questions set for the support request.")
            return

        await ctx.author.send("Starting your request for a support buddy. Please answer the following questions:")

        responses = {}
        for question in questions:
            await ctx.author.send(f"Question: {question}")
            try:
                response = await self.bot.wait_for(
                    "message",
                    check=lambda m: m.author == ctx.author and isinstance(m.channel, discord.DMChannel),
                    timeout=300
                )
                responses[question] = response.content
            except TimeoutError:
                await ctx.author.send("You took too long to respond. Please try again later.")
                return

        async with self.config.guild(ctx.guild).buddy_pending_requests() as buddy_pending_requests:
            buddy_pending_requests[str(ctx.author.id)] = responses

        requests_channel_id = await self.config.guild(ctx.guild).requests_channel()
        requests_channel = self.bot.get_channel(requests_channel_id)

        if requests_channel:
            embed = discord.Embed(title=f"New Support Request - {ctx.author.display_name}", color=discord.Color.blue())
            for question, response in responses.items():
                embed.add_field(name=f"Question: {question}", value=f"Response: {response}", inline=False)
            await requests_channel.send(embed=embed)
            await ctx.author.send("Your request has been submitted. A moderator will pair you with a support buddy soon.")
        else:
            await ctx.author.send("Requests channel not set. Please contact an admin.")

    @commands.guild_only()
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def buddypair(self, ctx, user_id: int, buddy_id: int):
        """Pair a user with a support buddy."""
        guild = ctx.guild
        user = guild.get_member(user_id)
        buddy = guild.get_member(buddy_id)

        if not user or not buddy:
            await ctx.send("Invalid user or buddy ID.")
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True),
            buddy: discord.PermissionOverwrite(read_messages=True)
        }

        category = discord.utils.get(guild.categories, name="Support Buddies")
        if not category:
            category = await guild.create_category("Buddy Support Networking")

        channel = await guild.create_text_channel(f"{user.name}-buddy-support", overwrites=overwrites, category=category)
        await channel.send(f"Hello {user.mention}! Your buddy is {buddy.mention}! Please, anything you need just ask them!")

        async with self.config.guild(ctx.guild).buddy_pending_requests() as buddy_pending_requests:
            if str(user.id) in buddy_pending_requests:
                del buddy_pending_requests[str(user.id)]

        await ctx.send(f"{user.name} has been paired with {buddy.name}.")

    @commands.guild_only()
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def buddyreqs(self, ctx):
        """List all pending support requests."""
        buddy_pending_requests = await self.config.guild(ctx.guild).buddy_pending_requests()
        if not buddy_pending_requests:
            await ctx.send("There are no pending support requests.")
            return

        for user_id, answers in buddy_pending_requests.items():
            user = ctx.guild.get_member(int(user_id))
            if user:
                await ctx.send(f"{user.mention} - {answers}")

    @commands.guild_only()
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def setqs(self, ctx, *questions):
        """Set the questions for support requests."""
        if not questions:
            await ctx.send("You must provide at least one question.")
            return

        await self.config.guild(ctx.guild).buddy_questions.set(list(questions))
        await ctx.send("Support request questions have been updated.")

    @commands.guild_only()
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def setbuddyreqchannel(self, ctx, channel: discord.TextChannel):
        """Set the channel for support request notifications."""
        await self.config.guild(ctx.guild).requests_channel.set(channel.id)
        await ctx.send(f"Requests channel has been set to {channel.mention}.")

    @commands.guild_only()
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def setreactionmsg(self, ctx, message_id: int):
        """Set the message ID to watch for reactions."""
        await self.config.guild(ctx.guild).reaction_message_id.set(message_id)
        reaction_emoji = await self.config.guild(ctx.guild).reaction_emoji()
        message = await ctx.fetch_message(message_id)
        await message.add_reaction(reaction_emoji)
        await ctx.send(f"Reaction message ID has been set to {message_id} and reacted with {reaction_emoji}.")

    @commands.guild_only()
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def setreactionemoji(self, ctx, emoji: str):
        """Set the emoji to watch for reactions."""
        await self.config.guild(ctx.guild).reaction_emoji.set(emoji)
        reaction_message_id = await self.config.guild(ctx.guild).reaction_message_id()
        if reaction_message_id:
            message = await ctx.fetch_message(reaction_message_id)
            await message.clear_reactions()
            await message.add_reaction(emoji)
        await ctx.send(f"Reaction emoji has been set to {emoji}.")

    @commands.guild_only()
    @commands.command()
    async def icebreakers(self, ctx):
        """Display a random icebreaker topic."""
        icebreaker = self.get_random_icebreaker()
        if icebreaker:
            await ctx.send(f"Icebreaker topic: {icebreaker}")
        else:
            await ctx.send("Could not fetch icebreaker topics at this time. Please try again later.")

    def get_random_icebreaker(self):
        """Fetch a random icebreaker topic from the internet."""
        try:
            url = "https://conversationstartersworld.com/250-conversation-starters/"
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            topics = soup.find_all("h2", class_="su-spoiler-title")
            if topics:
                return topics[0].text.strip()  # Return the first topic found
            else:
                return None
        except Exception as e:
            print(f"Error fetching icebreaker topics: {e}")
            return None
