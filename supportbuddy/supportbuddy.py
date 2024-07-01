import discord
from redbot.core import commands, Config
from redbot.core.bot import Red

class SupportBuddy(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "pending_requests": [],
            "questions": [
                "What is your name?",
                "What is your age?",
                "What are you seeking support for?"
            ],
            "icebreakers": [
                "What's your favorite hobby?",
                "What's a fun fact about yourself?",
                "If you could travel anywhere, where would you go?"
            ],
            "notification_channel": None
        }
        self.config.register_guild(**default_guild)

    @commands.command()
    async def buddyreq(self, ctx):
        """Request a support buddy."""
        questions = await self.config.guild(ctx.guild).questions()
        answers = []

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        for question in questions:
            await ctx.send(question)
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=60)
                answers.append(msg.content)
            except TimeoutError:
                await ctx.send("You took too long to respond. Please try again.")
                return

        await self.config.guild(ctx.guild).pending_requests.set_raw(ctx.author.id, value=answers)
        await ctx.send("Your request has been submitted. A moderator will pair you with a support buddy soon.")

        notification_channel_id = await self.config.guild(ctx.guild).notification_channel()
        if notification_channel_id:
            notification_channel = self.bot.get_channel(notification_channel_id)
            if notification_channel:
                await notification_channel.send(f"{ctx.author.mention} has requested a support buddy.")

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
            category = await guild.create_category("Support Buddies")

        channel = await guild.create_text_channel(f"{user.name}-support", overwrites=overwrites, category=category)
        await channel.send(f"Hello {user.mention} and {buddy.mention}, you have been paired for support!")

        await self.config.guild(ctx.guild).pending_requests.clear_raw(user.id)
        await ctx.send(f"{user.mention} has been paired with {buddy.mention}.")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def buddyreqs(self, ctx):
        """List all pending support requests."""
        pending_requests = await self.config.guild(ctx.guild).pending_requests()
        if not pending_requests:
            await ctx.send("There are no pending support requests.")
            return

        for user_id, answers in pending_requests.items():
            user = ctx.guild.get_member(int(user_id))
            if user:
                await ctx.send(f"{user.mention} - {answers}")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def setqs(self, ctx, *questions):
        """Set the questions for support requests."""
        if not questions:
            await ctx.send("You must provide at least one question.")
            return

        await self.config.guild(ctx.guild).questions.set(list(questions))
        await ctx.send("Support request questions have been updated.")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def setbuddyreqchannel(self, ctx, channel: discord.TextChannel):
        """Set the channel for support request notifications."""
        await self.config.guild(ctx.guild).notification_channel.set(channel.id)
        await ctx.send(f"Notification channel has been set to {channel.mention}.")

    @commands.command()
    async def icebreakers(self, ctx):
        """Display a list of icebreaker topics."""
        icebreakers = await self.config.guild(ctx.guild).icebreakers()
        if not icebreakers:
            await ctx.send("There are no icebreaker topics set.")
            return

        await ctx.send("Here are some icebreaker topics to get the conversation started:")
        for topic in icebreakers:
            await ctx.send(f"- {topic}")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def addicebreaker(self, ctx, *, topic):
        """Add an icebreaker topic."""
        async with self.config.guild(ctx.guild).icebreakers() as icebreakers:
            icebreakers.append(topic)
        await ctx.send("Icebreaker topic has been added.")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def remicebreaker(self, ctx, *, topic):
        """Remove an icebreaker topic."""
        async with self.config.guild(ctx.guild).icebreakers() as icebreakers:
            if topic in icebreakers:
                icebreakers.remove(topic)
                await ctx.send("Icebreaker topic has been removed.")
            else:
                await ctx.send("That topic is not in the list of icebreakers.")
