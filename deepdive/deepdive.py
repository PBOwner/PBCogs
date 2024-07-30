import discord
from redbot.core import commands, Config, bot
from textblob import TextBlob
from sklearn.feature_extraction.text import TfidfVectorizer
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import asyncio

Base = declarative_base()

class Result(Base):
    __tablename__ = 'results'
    id = Column(Integer, primary_key=True)
    platform = Column(String, nullable=False)
    result = Column(Text, nullable=False)

class DeepDive(commands.Cog):
    """Perform a deep dive to find information about a user"""

    def __init__(self, bot: bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_global(db_path='deepdive_results.sqlite', other_bots=[])
        self.tfidf_vectorizer = TfidfVectorizer()
        self.db_path = None
        self.engine = None
        self.Session = None

    @commands.command(name="deepdive")
    async def deepdive(self, ctx: commands.Context, username: str):
        """Perform a deep dive to find information about a user"""
        await ctx.author.send(f"Starting deep dive on {username}...")

        # Setup database
        self.db_path = await self.config.db_path()
        self._setup_db()
        await self._sync_db()

        # Notify other bots and perform local deep dive
        await self._notify_other_bots(username, ctx)
        await self._perform_local_deep_dive(username, ctx)

        # Fetch and compile results
        results = await self._fetch_results()
        embed = self._create_results_embed(username, results)

        await ctx.author.send(embed=embed)
        await self._close_db()

    @commands.command(name="addbot")
    async def add_bot(self, ctx: commands.Context, name: str, token: str):
        """Add a bot to the list of other bots"""
        async with self.config.other_bots() as other_bots:
            other_bots.append({'name': name, 'token': token})
        await ctx.author.send(f"Bot {name} added successfully.")

    @commands.command(name="removebot")
    async def remove_bot(self, ctx: commands.Context, name: str):
        """Remove a bot from the list of other bots"""
        async with self.config.other_bots() as other_bots:
            for bot in other_bots:
                if bot['name'] == name:
                    other_bots.remove(bot)
                    await ctx.author.send(f"Bot {name} removed successfully.")
                    return
            await ctx.author.send(f"Bot {name} not found.")

    def _setup_db(self):
        self.engine = create_engine(f'sqlite:///{self.db_path}')
        self.Session = sessionmaker(bind=self.engine)

    async def _sync_db(self):
        Base.metadata.create_all(self.engine)

    async def _notify_other_bots(self, username, ctx):
        other_bots = await self.config.other_bots()
        for bot_info in other_bots:
            await self._notify_bot(bot_info, username, ctx)

    async def _notify_bot(self, bot_info, username, ctx):
        bot_client = discord.Client(intents=discord.Intents.default())

        @bot_client.event
        async def on_ready():
            try:
                await self._perform_local_deep_dive(username, ctx, bot_client)
            except Exception as e:
                print(f"Error with bot {bot_info['name']}: {e}")
            finally:
                await bot_client.close()

        await bot_client.start(bot_info['token'])

    async def _perform_local_deep_dive(self, username, ctx, client=None):
        if client is None:
            client = self.bot

        for guild in client.guilds:
            await self._search_guild(guild, username, ctx)

    async def _search_guild(self, guild, username, ctx):
        members = [member async for member in guild.fetch_members(limit=None)]
        users = [member for member in members if self._is_matching_user(member, username)]

        if users:
            messages = await self._fetch_user_messages(guild, users)
            result = self._analyze_messages(users, messages)
            await self._save_result('Discord', result)

    def _is_matching_user(self, member, username):
        if username.startswith('<@') and username.endswith('>'):
            username = username[2:-1]
            if username.startswith('!'):
                username = username[1:]

        try:
            user_id = int(username)
            return member.id == user_id
        except ValueError:
            return (member.name.lower() == username.lower() or
                    str(member) == username or
                    member.mention == username)

    async def _fetch_user_messages(self, guild, users):
        messages = []
        for channel in guild.text_channels:
            for user in users:
                async for message in channel.history(limit=100):
                    if message.author == user:
                        messages.append(message)
        return messages

    def _analyze_messages(self, users, messages):
        if not messages:
            return f"{', '.join([str(user) for user in users])}\n\nNo messages found."

        trustworthiness = self._evaluate_trustworthiness(messages)
        intent_summary = self._analyze_intent(messages)
        sentiment_summary = self._analyze_sentiment(messages)
        top_words = self._get_top_words(messages)
        avg_message_length = self._calculate_avg_message_length(messages)
        most_active_channels = self._get_most_active_channels(messages)
        most_mentioned_users = self._get_most_mentioned_users(messages)
        time_of_day_summary = self._get_time_of_day_summary(messages)

        return (f"{', '.join([str(user) for user in users])}\n\nTrustworthiness: {trustworthiness}\n\n"
                f"Intent Summary: {intent_summary}\n\nSentiment Summary: {sentiment_summary}\n\n"
                f"Top Words: {top_words}\n\nAverage Message Length: {avg_message_length}\n\n"
                f"Most Active Channels: {most_active_channels}\n\nMost Mentioned Users: {most_mentioned_users}\n\n"
                f"Activity by Time of Day: {time_of_day_summary}")

    def _evaluate_trustworthiness(self, messages):
        positive_keywords = ['thanks', 'please', 'help', 'support']
        negative_keywords = ['spam', 'scam', 'abuse', 'hate']

        positive_score = sum(1 for msg in messages if any(kw in msg.content.lower() for kw in positive_keywords))
        negative_score = sum(1 for msg in messages if any(kw in msg.content.lower() for kw in negative_keywords))

        total_messages = len(messages)
        positive_ratio = positive_score / total_messages
        negative_ratio = negative_score / total_messages

        if negative_ratio > 0.1:
            return 'Untrustworthy'
        elif positive_ratio > 0.1:
            return 'Trustworthy'
        else:
            return 'Neutral'

    def _analyze_sentiment(self, messages):
        sentiments = [TextBlob(msg.content).sentiment.polarity for msg in messages]
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0

        if avg_sentiment > 0:
            return 'Overall Positive'
        elif avg_sentiment < 0:
            return 'Overall Negative'
        else:
            return 'Neutral'

    def _analyze_intent(self, messages):
        intent_keywords = {
            'seekingHelp': ['help', 'support', 'assist', 'issue', 'problem'],
            'offeringHelp': ['assist', 'help', 'support', 'aid', 'offer'],
            'promotion': ['check out', 'subscribe', 'follow', 'buy', 'join'],
            'casual': ['hello', 'hi', 'hey', 'lol', 'haha']
        }

        intents = {intent: 0 for intent in intent_keywords}
        for msg in messages:
            for intent, keywords in intent_keywords.items():
                if any(kw in msg.content.lower() for kw in keywords):
                    intents[intent] += 1

        return '\n'.join([f"{intent}: {count}" for intent, count in intents.items()])

    def _get_top_words(self, messages):
        tfidf_matrix = self.tfidf_vectorizer.fit_transform([msg.content for msg in messages])
        feature_names = self.tfidf_vectorizer.get_feature_names_out()
        top_words = [feature_names[i] for i in tfidf_matrix[0].nonzero()[1]]
        return ', '.join(top_words)

    def _calculate_avg_message_length(self, messages):
        total_length = sum(len(msg.content) for msg in messages)
        return round(total_length / len(messages), 2) if messages else 0

    def _get_most_active_channels(self, messages):
        channel_activity = {}
        for msg in messages:
            channel_activity[msg.channel.name] = channel_activity.get(msg.channel.name, 0) + 1
        return self._get_top_entries(channel_activity, 5)

    def _get_most_mentioned_users(self, messages):
        mention_activity = {}
        for msg in messages:
            for mention in msg.mentions:
                mention_activity[mention.name] = mention_activity.get(mention.name, 0) + 1
        return self._get_top_entries(mention_activity, 5)

    def _get_time_of_day_summary(self, messages):
        time_of_day_activity = [0] * 24
        for msg in messages:
            time_of_day_activity[msg.created_at.hour] += 1
        return '\n'.join([f"{hour}:00 - {hour+1}:00: {count}" for hour, count in enumerate(time_of_day_activity)])

    def _get_top_entries(self, data, limit):
        sorted_entries = sorted(data.items(), key=lambda item: item[1], reverse=True)
        return ', '.join([f"{entry[0]}: {entry[1]}" for entry in sorted_entries[:limit]])

    async def _save_result(self, platform, result):
        session = self.Session()
        new_result = Result(platform=platform, result=result)
        session.add(new_result)
        session.commit()
        session.close()

    async def _fetch_results(self):
        session = self.Session()
        results = session.query(Result).all()
        session.close()
        return results

    async def _close_db(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _create_results_embed(self, username, results):
        embed = discord.Embed(title=f"Deep Dive Results for {username}", color=0x0099ff)
        for result in results:
            embed.add_field(name=result.platform, value=result.result, inline=False)
        return embed

def setup(bot):
    bot.add_cog(DeepDive(bot))
