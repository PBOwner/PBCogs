import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
import fetch
import Sentiment
import natural
import asyncio

sentiment = Sentiment.SentimentIntensityAnalyzer()
TfIdf = natural.TfIdf

class DeepDive(commands.Cog):
    """Cog to perform a deep dive to find information about a user."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567892, force_registration=True)
        default_global = {
            "requests": {}
        }
        self.config.register_global(**default_global)

    @commands.command()
    async def deepdive(self, ctx: commands.Context, username: str):
        """Perform a deep dive to find information about a user."""
        await ctx.send(f"Performing a deep dive on {username}...")

        results = await self.perform_deep_dive(username, ctx)

        embed = discord.Embed(
            title=f"Deep Dive Results for {username}",
            color=discord.Color.blue()
        )

        for result in results:
            embed.add_field(name=result['platform'], value=result['result'])

        await ctx.send(embed=embed)

    async def perform_deep_dive(self, username, ctx):
        search_functions = [
            self.search_discord,
            self.search_youtube
        ]

        results = []
        for search_function in search_functions:
            platform_name = self.get_platform_name(search_functions.index(search_function))
            await ctx.send(f"Performing a deep dive on {username}... (Searching {platform_name})")
            result = await search_function(username, ctx)
            results.append({
                "platform": platform_name,
                "result": result
            })

        return results

    def get_platform_name(self, index):
        if index == 0:
            return 'Discord'
        elif index == 1:
            return 'YouTube'
        else:
            return 'Unknown'

    def create_progress_bar(self, current, total, size=20):
        progress = round((current / total) * size)
        empty_progress = size - progress

        progress_text = '█' * progress
        empty_progress_text = '░' * empty_progress

        return f"{progress_text}{empty_progress_text} {current}/{total}"

    async def search_discord(self, query, ctx):
        try:
            guilds = self.bot.guilds
            found_users = []
            messages = []
            message_count = 0
            total_message_length = 0
            total_messages = 0
            channel_activity = {}
            mention_activity = {}
            time_of_day_activity = [0] * 24
            tfidf = TfIdf()

            checked_servers = 0
            total_servers = len(guilds)

            # Calculate total messages to be checked
            for guild in guilds:
                members = await guild.fetch_members().flatten()
                users = [member for member in members if query.lower() in member.name.lower() or query.lower() in member.display_name.lower()]

                for user in users:
                    user_messages = await self.fetch_user_messages(guild, user.id)
                    total_messages += len(user_messages)

            for guild in guilds:
                checked_servers += 1
                embed = discord.Embed(
                    title='Checking',
                    description=f"Out of {total_servers} servers, I have checked {checked_servers} servers. (Phase: Searching {guild.name})"
                )
                embed.add_field(name='DeepDive Progress', value=self.create_progress_bar(checked_servers, total_servers), inline=True)
                embed.add_field(name='Message Count', value=f"Checking {message_count}/{total_messages} messages", inline=True)
                embed.add_field(name='Username', value=query, inline=True)

                await ctx.send(embed=embed)

                members = await guild.fetch_members().flatten()
                users = [member for member in members if query.lower() in member.name.lower() or query.lower() in member.display_name.lower()]

                for user in users:
                    found_users.append(f"{user.name}#{user.discriminator} in guild {guild.name}")

                    user_messages = await self.fetch_user_messages(guild, user.id)

                    if user_messages:
                        messages.extend(user_messages)
                        total_message_length += sum(len(msg['content']) for msg in user_messages)

                        for i, msg in enumerate(user_messages):
                            message_count += 1
                            channel = msg['channel']
                            channel_activity[channel] = channel_activity.get(channel, 0) + 1

                            for mention in msg['mentions']:
                                mention_activity[mention] = mention_activity.get(mention, 0) + 1

                            hour = msg['created_at'].hour
                            time_of_day_activity[hour] += 1
                            tfidf.add_document(msg['content'])

                            embed = discord.Embed(
                                title='Checking',
                                description=f"Out of {total_servers} servers, I have checked {checked_servers} servers. (Phase: Searching {guild.name})"
                            )
                            embed.add_field(name='DeepDive Progress', value=self.create_progress_bar(checked_servers, total_servers), inline=True)
                            embed.add_field(name='Message Count', value=f"Checking {message_count}/{total_messages} messages", inline=True)
                            embed.add_field(name='Username', value=query, inline=True)

                            await ctx.send(embed=embed)

            if found_users and messages:
                trustworthiness = self.evaluate_trustworthiness(messages)
                intent_summary = self.analyze_intent(messages)
                sentiment_summary = self.analyze_sentiment(messages)
                top_words = self.get_top_words(tfidf)
                avg_message_length = round(total_message_length / message_count, 2)
                most_active_channels = self.get_top_entries(channel_activity, 5)
                most_mentioned_users = self.get_top_entries(mention_activity, 5)
                time_of_day_summary = self.get_time_of_day_summary(time_of_day_activity)

                return (f"{', '.join(found_users)}\n\nTrustworthiness: {trustworthiness}\n\n"
                        f"Intent Summary: {intent_summary}\n\nSentiment Summary: {sentiment_summary}\n\n"
                        f"Top Words and Phrases: {top_words}\n\nAverage Message Length: {avg_message_length}\n\n"
                        f"Most Active Channels: {most_active_channels}\n\nMost Mentioned Users: {most_mentioned_users}\n\n"
                        f"Activity by Time of Day: {time_of_day_summary}")
            elif found_users:
                return f"{', '.join(found_users)}\n\nNo messages found for this user."
            else:
                return 'No Discord user found with that query'
        except Exception as error:
            await ctx.send(f"Error searching Discord: {error}")
            return 'Error searching Discord'

    async def fetch_user_messages(self, guild, user_id):
        messages = []
        channels = [channel for channel in guild.text_channels if channel.permissions_for(guild.me).read_messages]

        for channel in channels:
            try:
                fetched_messages = await channel.history(limit=100).flatten()
            except discord.Forbidden:
                continue

            user_messages = [msg for msg in fetched_messages if msg.author.id == user_id]
            for msg in user_messages:
                messages.append({
                    'content': msg.content,
                    'created_at': msg.created_at,
                    'channel': msg.channel.name,
                    'mentions': [mention.name for mention in msg.mentions]
                })

            await asyncio.sleep(1)  # Add delay to avoid hitting rate limits

        return messages

    def evaluate_trustworthiness(self, messages):
        if not messages:
            return 'Not enough data'
        positive_keywords = ['thanks', 'please', 'help', 'support']
        negative_keywords = ['spam', 'scam', 'abuse', 'hate']

        positive_score = 0
        negative_score = 0

        for message in messages:
            for keyword in positive_keywords:
                if keyword in message['content'].lower():
                    positive_score += 1
            for keyword in negative_keywords:
                if keyword in message['content'].lower():
                    negative_score += 1

        total_messages = len(messages)
        positive_ratio = positive_score / total_messages
        negative_ratio = negative_score / total_messages

        if negative_ratio > 0.1:
            return 'Untrustworthy'
        elif positive_ratio > 0.1:
            return 'Trustworthy'
        else:
            return 'Neutral'

    def analyze_sentiment(self, messages):
        if not messages:
            return 'Not enough data'

        sentiment_results = [sentiment.polarity_scores(message['content'])['compound'] for message in messages]
        average_score = sum(sentiment_results) / len(sentiment_results)

        if average_score > 0:
            return 'Overall Positive'
        elif average_score < 0:
            return 'Overall Negative'
        else:
            return 'Neutral'

    def analyze_intent(self, messages):
        if not messages:
            return 'Not enough data'
        intent_keywords = {
            'seekingHelp': ['help', 'support', 'assist', 'issue', 'problem'],
            'offeringHelp': ['assist', 'help', 'support', 'aid', 'offer'],
            'promotion': ['check out', 'subscribe', 'follow', 'buy', 'join'],
            'casual': ['hello', 'hi', 'hey', 'lol', 'haha']
        }

        intents = {
            'seekingHelp': 0,
            'offeringHelp': 0,
            'promotion': 0,
            'casual': 0,
        }

        for message in messages:
            for intent in intent_keywords:
                for keyword in intent_keywords[intent]:
                    if keyword in message['content'].lower():
                        intents[intent] += 1

        summary = 'Intentions:\n'
        for intent, count in intents.items():
            summary += f"{intent}: {count} messages\n"

        return summary

    def get_top_words(self, tfidf):
        top_words = [term['term'] for term in tfidf.list_terms(0) if term['tfidf'] > 0.1]
        return ', '.join(top_words)

    def get_top_entries(self, data, limit):
        sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)
        return ', '.join([f"{key}: {value}" for key, value in sorted_data[:limit]])

    def get_time_of_day_summary(self, activity):
        return '\n'.join([f"{hour}:00 - {hour + 1}:00: {count}" for hour, count in enumerate(activity)])

    async def search_youtube(self, username):
        api_key = 'YOUR_YOUTUBE_API_KEY'  # Replace with your YouTube Data API key
        api_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=channel&q={username}&key={api_key}"

        try:
            response = await fetch(api_url)
            data = await response.json()

            if not data['items']:
                return f"No YouTube channel found for username: {username}"

            channel = data['items'][0]
            return (f"Found YouTube channel: [{channel['snippet']['title']}]"
                    f"(https://www.youtube.com/channel/{channel['id']['channelId']}) - {channel['snippet']['description']}")
        except Exception as error:
            await ctx.send(f"Error searching YouTube: {error}")
            return 'Error searching YouTube'


def setup(bot: Red):
    bot.add_cog(DeepDive(bot))
