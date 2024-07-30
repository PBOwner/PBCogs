import discord
from redbot.core import commands, Config, bot
from textblob import TextBlob
from sklearn.feature_extraction.text import TfidfVectorizer
from sqlalchemy import create_engine, Column, Integer, String, Text, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import os
import asyncio
import json
from collections import defaultdict

Base = declarative_base()

class Result(Base):
    __tablename__ = 'results'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
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
        self.metadata = MetaData()

    @commands.command(name="deepdive")
    async def deepdive(self, ctx: commands.Context, username: str):
        """Perform a deep dive to find information about a user"""
        progress_message = await ctx.author.send(f"Starting deep dive on {username}...")

        # Setup database
        self.db_path = await self.config.db_path()
        self._setup_db()

        await progress_message.edit(content=f"Database setup complete for {username}. Notifying other bots...")

        # Notify other bots and perform local deep dive
        await self._notify_other_bots(username, ctx, progress_message)
        await self._perform_local_deep_dive(username, ctx, progress_message)

        await progress_message.edit(content=f"Deep dive in progress for {username}. Fetching results...")

        # Fetch and compile results
        results = await self._fetch_results(username)
        aggregated_results = self._aggregate_results(results)
        embeds = self._create_results_embeds(username, aggregated_results)

        for embed in embeds:
            await ctx.author.send(embed=embed)

        # Close the database
        await self._close_db()

        await progress_message.edit(content=f"Deep dive complete for {username}.")

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
        # Create the results table if it doesn't exist
        if not self.engine.dialect.has_table(self.engine, 'results'):
            Base.metadata.create_all(self.engine)
        else:
            # Check if the existing table has the correct schema
            with self.engine.connect() as conn:
                result = conn.execute("PRAGMA table_info(results)").fetchall()
                columns = [row[1] for row in result]
                if 'user_id' not in columns:
                    # Drop the existing table and recreate it
                    conn.execute("DROP TABLE results")
                    Base.metadata.create_all(self.engine)

    async def _notify_other_bots(self, username, ctx, progress_message):
        other_bots = await self.config.other_bots()
        for i, bot_info in enumerate(other_bots):
            await self._notify_bot(bot_info, username, ctx, progress_message, i + 1, len(other_bots))

    async def _notify_bot(self, bot_info, username, ctx, progress_message, current, total):
        bot_client = discord.Client(intents=discord.Intents.default())

        @bot_client.event
        async def on_ready():
            try:
                await self._perform_local_deep_dive(username, ctx, progress_message, bot_client)
            except Exception as e:
                await ctx.author.send(f"Error with bot {bot_info['name']}: {e}")
            finally:
                await bot_client.close()

        await bot_client.start(bot_info['token'])

        # Update progress
        progress = self._create_progress_bar(current, total)
        await progress_message.edit(content=f"Gathering information from {bot_info['name']}...\n**Progress:** {progress}")

    def _create_progress_bar(self, current, total, size=20):
        progress = round((current / total) * size)
        empty_progress = size - progress

        progress_text = '' * progress
        empty_progress_text = '' * empty_progress

        return f"[{progress_text}{empty_progress_text}] {current}/{total}"

    async def _perform_local_deep_dive(self, username, ctx, progress_message, client=None):
        if client is None:
            client = self.bot

        total_guilds = len(client.guilds)
        for i, guild in enumerate(client.guilds, start=1):
            await self._search_guild(guild, username, ctx)
            progress = self._create_progress_bar(i, total_guilds)
            await progress_message.edit(content=f"Deep dive in progress for {username}. Searched {i}/{total_guilds} servers...\n**Progress:** {progress}")

    async def _search_guild(self, guild, username, ctx):
        members = [member async for member in guild.fetch_members(limit=None)]
        users = [member for member in members if self._is_matching_user(member, username)]

        if users:
            messages = await self._fetch_user_messages(guild, users)
            result = self._analyze_messages(users, messages, guild.name)
            await self._save_result(users[0].id, 'Discord', result)

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

    def _analyze_messages(self, users, messages, guild_name):
        if not messages:
            return json.dumps({
                'users': ', '.join([str(user) for user in users]),
                'servers': [guild_name],
                'trustworthiness': 'Neutral',
                'intent_summary': {},
                'sentiment_summary': 'Neutral',
                'top_words': '',
                'avg_message_length': 0,
                'most_active_channels': {},
                'most_mentioned_users': {},
                'time_of_day_summary': [0] * 24
            })

        trustworthiness = self._evaluate_trustworthiness(messages)
        intent_summary = self._analyze_intent(messages)
        sentiment_summary = self._analyze_sentiment(messages)
        top_words = self._get_top_words(messages)
        avg_message_length = self._calculate_avg_message_length(messages)
        most_active_channels = self._get_most_active_channels(messages)
        most_mentioned_users = self._get_most_mentioned_users(messages)
        time_of_day_summary = self._get_time_of_day_summary(messages)

        return json.dumps({
            'users': ', '.join([str(user) for user in users]),
            'servers': [guild_name],
            'trustworthiness': trustworthiness,
            'intent_summary': intent_summary,
            'sentiment_summary': sentiment_summary,
            'top_words': top_words,
            'avg_message_length': avg_message_length,
            'most_active_channels': most_active_channels,
            'most_mentioned_users': most_mentioned_users,
            'time_of_day_summary': time_of_day_summary
        })

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

        return intents

    def _get_top_words(self, messages):
        filtered_messages = [msg.content for msg in messages if msg.content.strip() and not all(word in self.tfidf_vectorizer.get_stop_words() for word in msg.content.split())]
        if not filtered_messages:
            return 'No significant words found.'

        tfidf_matrix = self.tfidf_vectorizer.fit_transform(filtered_messages)
        feature_names = self.tfidf_vectorizer.get_feature_names_out()
        top_words = [feature_names[i] for i in tfidf_matrix[0].nonzero()[1]]
        return ', '.join(top_words)

    def _calculate_avg_message_length(self, messages):
        total_length = sum(len(msg.content) for msg in messages)
        return round(total_length / len(messages), 2) if messages else 0

    def _get_most_active_channels(self, messages):
        channel_activity = defaultdict(int)
        for msg in messages:
            channel_activity[msg.channel.name] += 1
        return channel_activity

    def _get_most_mentioned_users(self, messages):
        mention_activity = defaultdict(int)
        for msg in messages:
            for mention in msg.mentions:
                mention_activity[mention.name] += 1
        return mention_activity

    def _get_time_of_day_summary(self, messages):
        time_of_day_activity = [0] * 24
        for msg in messages:
            time_of_day_activity[msg.created_at.hour] += 1
        return time_of_day_activity

    def _aggregate_results(self, results):
        aggregated = {
            'users': '',
            'servers': set(),
            'trustworthiness': defaultdict(int),
            'intent_summary': defaultdict(int),
            'sentiment_summary': defaultdict(int),
            'top_words': [],
            'avg_message_length': 0,
            'most_active_channels': defaultdict(int),
            'most_mentioned_users': defaultdict(int),
            'time_of_day_summary': [0] * 24
        }
        total_messages = 0

        for result in results:
            result_data = json.loads(result.result)
            aggregated['users'] = result_data['users']
            aggregated['servers'].update(result_data['servers'])

            if result_data['trustworthiness']:
                aggregated['trustworthiness'][result_data['trustworthiness']] += 1

            for intent, count in result_data['intent_summary'].items():
                aggregated['intent_summary'][intent] += count

            aggregated['sentiment_summary'][result_data['sentiment_summary']] += 1
            aggregated['top_words'].extend(result_data['top_words'].split(', '))
            aggregated['avg_message_length'] += result_data['avg_message_length'] * len(result_data['top_words'].split(', '))
            for channel, count in result_data['most_active_channels'].items():
                aggregated['most_active_channels'][channel] += count
            for user, count in result_data['most_mentioned_users'].items():
                aggregated['most_mentioned_users'][user] += count
            for hour, count in enumerate(result_data['time_of_day_summary']):
                aggregated['time_of_day_summary'][hour] += count
            total_messages += len(result_data['top_words'].split(', '))

        aggregated['avg_message_length'] /= total_messages if total_messages else 1
        aggregated['top_words'] = ', '.join(self.tfidf_vectorizer.get_feature_names_out()[:10])
        aggregated['servers'] = ', '.join(aggregated['servers'])
        return aggregated

    def _create_results_embeds(self, username, aggregated_results):
        embeds = []
        embed = discord.Embed(title=f"Deep Dive Results for {username}", color=0x0099ff)
        total_length = 0

        fields = [
            ("Users", aggregated_results['users']),
            ("Servers", aggregated_results['servers']),
            ("Trustworthiness", ', '.join([f"{k}: {v}" for k, v in aggregated_results['trustworthiness'].items()])),
            ("Intent Summary", ', '.join([f"{k}: {v}" for k, v in aggregated_results['intent_summary'].items()])),
            ("Sentiment Summary", ', '.join([f"{k}: {v}" for k, v in aggregated_results['sentiment_summary'].items()])),
            ("Top Words", aggregated_results['top_words']),
            ("Average Message Length", str(aggregated_results['avg_message_length'])),
            ("Most Active Channels", ', '.join([f"{k}: {v}" for k, v in aggregated_results['most_active_channels'].items()])),
            ("Most Mentioned Users", ', '.join([f"{k}: {v}" for k, v in aggregated_results['most_mentioned_users'].items()])),
            ("Activity by Time of Day", ', '.join([f"{hour}:00 - {hour+1}:00: {count}" for hour, count in enumerate(aggregated_results['time_of_day_summary'])]))
        ]

        for name, value in fields:
            if len(value) > 1024:
                value = value[:1021] + "..."

            field_length = len(name) + len(value)
            if total_length + field_length > 6000:
                embeds.append(embed)
                embed = discord.Embed(title=f"Deep Dive Results for {username}", color=0x0099ff)
                total_length = 0

            embed.add_field(name=name, value=value, inline=False)
            total_length += field_length

        embeds.append(embed)
        return embeds

    async def _save_result(self, user_id, platform, result):
        session = self.Session()
        new_result = Result(
            user_id=user_id,
            platform=platform,
            result=result
        )
        session.add(new_result)
        session.commit()
        session.close()

    async def _fetch_results(self, username):
        session = self.Session()
        results = session.query(Result).filter(Result.user_id == username).all()
        session.close()
        return results

    async def _close_db(self):
        if self.engine:
            self.engine.dispose()

def setup(bot):
    bot.add_cog(DeepDive(bot))
