import discord
from redbot.core import commands, Config, bot
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS
from textblob import TextBlob
from sklearn.feature_extraction.text import TfidfVectorizer
import sqlite3
import os
import asyncio

class DeepDive(commands.Cog):
    """Perform a deep dive to find information about a user"""

    def __init__(self, bot: bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_global(db_path='deepdive_results.sqlite', other_bots=[])
        self.db_path = self.bot.loop.run_until_complete(self.config.db_path())
        self.tfidf_vectorizer = TfidfVectorizer()

    @commands.command(name="deepdive")
    async def deepdive(self, ctx: commands.Context, username: str):
        """Perform a deep dive to find information about a user"""
        await ctx.send(f"Performing a deep dive on {username}...")

        await self._sync_db()

        # Notify other bots to start their process one by one
        await self._notify_other_bots_sequentially(username, ctx)

        # Perform the local deep dive
        await self._perform_deep_dive(username, ctx)

        # Fetch and compile results
        results = await self._fetch_results()
        combined_results = [{'platform': result[0], 'result': result[1]} for result in results]

        embed = discord.Embed(title=f"Deep Dive Results for {username}", color=0x0099ff)
        for result in combined_results:
            embed.add_field(name=result['platform'], value=result['result'], inline=False)

        await ctx.send(embed=embed)

        # Delete the database file
        await self._close_db()

    @commands.command(name="addbot")
    async def add_bot(self, ctx: commands.Context, name: str, token: str):
        """Add a bot to the list of other bots"""
        async with self.config.other_bots() as other_bots:
            other_bots.append({'name': name, 'token': token})
        await ctx.send(f"Bot {name} added successfully.")

    @commands.command(name="removebot")
    async def remove_bot(self, ctx: commands.Context, name: str):
        """Remove a bot from the list of other bots"""
        async with self.config.other_bots() as other_bots:
            for bot in other_bots:
                if bot['name'] == name:
                    other_bots.remove(bot)
                    await ctx.send(f"Bot {name} removed successfully.")
                    return
            await ctx.send(f"Bot {name} not found.")

    async def _sync_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS Result (platform TEXT, result TEXT)''')
        conn.commit()
        conn.close()

    async def _notify_other_bots_sequentially(self, username, ctx):
        other_bots = await self.config.other_bots()

        for i, bot_info in enumerate(other_bots):
            progress = self._create_progress_bar(i + 1, len(other_bots))

            embed = discord.Embed(title="Progress", description=f"**Progress:** {progress}", color=0x0099ff)
            await ctx.send(f"Gathering information from {bot_info['name']}...", embed=embed)

            bot_client = discord.Client(intents=discord.Intents.default())

            @bot_client.event
            async def on_ready():
                print(f"{bot_info['name']} is ready!")
                try:
                    await self._perform_deep_dive(username, ctx, bot_client)
                except Exception as error:
                    print(f"Error performing deep dive with {bot_info['name']}: {error}")
                finally:
                    await bot_client.close()

            await bot_client.start(bot_info['token'])

    def _create_progress_bar(self, current, total, size=20):
        progress = round((current / total) * size)
        empty_progress = size - progress
        progress_text = '█' * progress
        empty_progress_text = '░' * empty_progress
        return f"`[{progress_text}{empty_progress_text}] {current}/{total}`"

    async def _perform_deep_dive(self, username, ctx, client=None):
        search_functions = [self._search_discord]

        for search_function in search_functions:
            platform_name = self._get_platform_name(search_functions.index(search_function))
            await ctx.send(f"Performing a deep dive on {username}... (Searching {platform_name})")
            try:
                result = await search_function(username, ctx, client)
                await self._save_result(platform_name, result)
            except Exception as error:
                print(f"Error performing search function {platform_name}: {error}")

    def _get_platform_name(self, index):
        if index == 0:
            return 'Discord'
        return 'Unknown'

    async def _search_discord(self, query, ctx, client):
        if client is None:
            client = self.bot

        guilds = client.guilds
        found_users = []
        messages = []
        message_count = 0
        total_message_length = 0
        total_messages = 0
        channel_activity = {}
        mention_activity = {}
        time_of_day_activity = [0] * 24

        checked_servers = 0
        total_servers = len(guilds)

        for guild in guilds:
            checked_servers += 1
            embed = discord.Embed(
                color=0x0099ff,
                title='Checking',
                description=f'Out of {total_servers} servers, I have checked {checked_servers} servers. (Phase: Searching {guild.name})'
            )
            embed.add_field(name='Deep Dive Progress', value=f'**Progress:** {self._create_progress_bar(checked_servers, total_servers)}', inline=False)
            embed.add_field(name='Message Count', value=f'**Checking:** {message_count}/{total_messages} messages', inline=False)
            embed.add_field(name='Username', value=f'**Query:** {query}', inline=False)
            embed.set_footer(text=guild.name, icon_url=guild.icon.url)
            await ctx.send(embed=embed)

            try:
                members = await guild.fetch_members(limit=None).flatten()
                users = [member for member in members if
                         member.name.lower() == query.lower() or
                         str(member) == query or
                         member.id == int(query) or
                         member.mention == query]

                if not users:
                    continue

                for user in users:
                    found_users.append(f"{user} in guild {guild.name}")
                    user_messages = await self._fetch_user_messages(guild, user.id)

                    if user_messages:
                        messages.extend(user_messages)
                        message_count += len(user_messages)
                        total_messages += len(user_messages)
                        total_message_length += sum(len(msg['content']) for msg in user_messages)

                        for msg in user_messages:
                            channel = msg['channel']
                            channel_activity[channel] = channel_activity.get(channel, 0) + 1

                            for mention in msg['mentions']:
                                mention_activity[mention] = mention_activity.get(mention, 0) + 1

                            hour = msg['created_at'].hour
                            time_of_day_activity[hour] += 1
                            self.tfidf_vectorizer.fit_transform([msg['content']])

            except Exception as error:
                print(f"Error searching in guild {guild.name}: {error}")
                continue

        if found_users and messages:
            trustworthiness = self._evaluate_trustworthiness(messages)
            intent_summary = self._analyze_intent(messages)
            sentiment_summary = self._analyze_sentiment(messages)
            top_words = self._get_top_words(messages)
            avg_message_length = round(total_message_length / message_count, 2)
            most_active_channels = self._get_top_entries(channel_activity, 5)
            most_mentioned_users = self._get_top_entries(mention_activity, 5)
            time_of_day_summary = self._get_time_of_day_summary(time_of_day_activity)

            return f"{', '.join(found_users)}\n\nTrustworthiness: {trustworthiness}\n\nIntent Summary: {intent_summary}\n\nSentiment Summary: {sentiment_summary}\n\nTop Words and Phrases: {top_words}\n\nAverage Message Length: {avg_message_length}\n\nMost Active Channels: {most_active_channels}\n\nMost Mentioned Users: {most_mentioned_users}\n\nActivity by Time of Day: {time_of_day_summary}"
        elif found_users:
            return f"{', '.join(found_users)}\n\nNo messages found for this user."
        else:
            return 'No Discord user found with that query'

    async def _fetch_user_messages(self, guild, user_id):
        messages = []
        channels = [channel for channel in guild.channels if channel.type == discord.ChannelType.text]

        for channel in channels:
            try:
                async for message in channel.history(limit=100):
                    if message.author.id == user_id:
                        messages.append({
                            'content': message.content,
                            'created_at': message.created_at,
                            'channel': channel.name,
                            'mentions': [mention.name for mention in message.mentions]
                        })
            except Exception as error:
                print(f"Error fetching messages in {channel.name}: {error}")
                continue

            await asyncio.sleep(1)

        return messages

    def _evaluate_trustworthiness(self, messages):
        if not messages:
            return 'Not enough data'
        positive_keywords = ['thanks', 'please', 'help', 'support']
        negative_keywords = ['spam', 'scam', 'abuse', 'hate']

        positive_score = sum(1 for message in messages if any(keyword in message['content'].lower() for keyword in positive_keywords))
        negative_score = sum(1 for message in messages if any(keyword in message['content'].lower() for keyword in negative_keywords))

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
        if not messages:
            return 'Not enough data'
        sentiment_results = [TextBlob(message['content']).sentiment for message in messages]
        average_score = sum(result.polarity for result in sentiment_results) / len(sentiment_results)

        if average_score > 0:
            return 'Overall Positive'
        elif average_score < 0:
            return 'Overall Negative'
        else:
            return 'Neutral'

    def _analyze_intent(self, messages):
        if not messages:
            return 'Not enough data'
        intent_keywords = {
            'seekingHelp': ['help', 'support', 'assist', 'issue', 'problem'],
            'offeringHelp': ['assist', 'help', 'support', 'aid', 'offer'],
            'promotion': ['check out', 'subscribe', 'follow', 'buy', 'join'],
            'casual': ['hello', 'hi', 'hey', 'lol', 'haha']
        }

        intents = {intent: 0 for intent in intent_keywords}

        for message in messages:
            for intent, keywords in intent_keywords.items():
                if any(keyword in message['content'].lower() for keyword in keywords):
                    intents[intent] += 1

        summary = 'Intentions:\n'
        for intent, count in intents.items():
            summary += f"{intent}: {count} messages\n"

        return summary

    def _get_top_words(self, messages):
        tfidf_matrix = self.tfidf_vectorizer.fit_transform([msg['content'] for msg in messages])
        feature_names = self.tfidf_vectorizer.get_feature_names_out()
        top_words = [feature_names[i] for i in tfidf_matrix[0].nonzero()[1]]
        return ', '.join(top_words)

    def _get_top_entries(self, data, limit):
        sorted_entries = sorted(data.items(), key=lambda item: item[1], reverse=True)
        return ', '.join([f"{entry[0]}: {entry[1]}" for entry in sorted_entries[:limit]])

    def _get_time_of_day_summary(self, activity):
        return '\n'.join([f"{hour}:00 - {hour+1}:00: {count}" for hour, count in enumerate(activity)])

    async def _save_result(self, platform, result):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO Result (platform, result) VALUES (?, ?)", (platform, result))
        conn.commit()
        conn.close()

    async def _fetch_results(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT * FROM Result")
        results = c.fetchall()
        conn.close()
        return results

    async def _close_db(self):
        os.remove(self.db_path)

def setup(bot):
    bot.add_cog(DeepDive(bot))
