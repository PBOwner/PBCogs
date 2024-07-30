import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
import sqlite3
import os
import asyncio
from collections import defaultdict, Counter
from datetime import datetime
from nltk import TfIdf
from textblob import TextBlob
from PIL import Image, ImageDraw

class DeepDive(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_global(db_path="deepdive_results.sqlite", other_bots=[])

    @commands.slash_command()
    async def deepdive(self, ctx: commands.Context, username: str):
        await ctx.send(f"Performing a deep dive on {username}...", ephemeral=True)

        db_path = await self.config.db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''CREATE TABLE IF NOT EXISTS Result (
            platform TEXT NOT NULL,
            result TEXT NOT NULL
        )''')
        conn.commit()

        try:
            await self.notify_other_bots_sequentially(username, ctx)
            await self.perform_deep_dive(username, ctx)

            cursor.execute("SELECT platform, result FROM Result")
            results = cursor.fetchall()

            embed = discord.Embed(title=f"Deep Dive Results for {username}", color=0x0099ff)
            for platform, result in results:
                embed.add_field(name=platform, value=result, inline=False)

            await ctx.send("Deep dive complete!", embed=embed, ephemeral=True)
        finally:
            conn.close()
            if os.path.exists(db_path):
                os.remove(db_path)

    @commands.slash_command()
    async def addbot(self, ctx: commands.Context, name: str, token: str):
        """Add a bot to the list of other bots"""
        async with self.config.other_bots() as other_bots:
            other_bots.append({'name': name, 'token': token})
        await ctx.send(f"Bot {name} added successfully.", ephemeral=True)

    @commands.slash_command()
    async def removebot(self, ctx: commands.Context, name: str):
        """Remove a bot from the list of other bots"""
        async with self.config.other_bots() as other_bots:
            for bot in other_bots:
                if bot['name'] == name:
                    other_bots.remove(bot)
                    await ctx.send(f"Bot {name} removed successfully.", ephemeral=True)
                    return
            await ctx.send(f"Bot {name} not found.", ephemeral=True)

    @commands.slash_command()
    async def listbots(self, ctx: commands.Context):
        """List all added bots"""
        other_bots = await self.config.other_bots()
        if not other_bots:
            await ctx.send("No bots added.", ephemeral=True)
        else:
            embed = discord.Embed(title="Added Bots", color=0x0099ff)
            for bot in other_bots:
                embed.add_field(name=bot['name'], value=bot['token'], inline=False)
            await ctx.send(embed=embed, ephemeral=True)

    async def notify_other_bots_sequentially(self, username, ctx):
        other_bots = await self.config.other_bots()

        for i, bot_info in enumerate(other_bots):
            progress_image_path = self._create_progress_image(i + 1, len(other_bots))
            embed = self._create_progress_embed(bot_info['name'], i + 1, len(other_bots), progress_image_path)
            await ctx.send(
                f"Gathering information from {bot_info['name']}...",
                embed=embed,
                ephemeral=True
            )

            bot_client = discord.Client(intents=discord.Intents.default())

            @bot_client.event
            async def on_ready():
                try:
                    await self.perform_deep_dive(username, ctx, bot_client)
                except Exception as e:
                    print(f"Error performing deep dive with {bot_info['name']}: {e}")
                finally:
                    await bot_client.close()

            await bot_client.start(bot_info['token'])

    def _create_progress_embed(self, currentserverchecking, checkedservers, totalservers, progress_image_path, message_count=0, total_messages=0, query=""):
        embed = discord.Embed(
            title="Checking",
            description=f"Out of {totalservers} servers, I have checked {checkedservers} servers. (Phase: Searching {currentserverchecking})",
            color=0x0099ff
        )
        embed.add_field(name="Deep Dive Progress", value="**Progress:**", inline=False)
        embed.set_image(url=f"attachment://{progress_image_path}")
        embed.add_field(name="Message Count", value=f"**Checking:** {message_count}/{total_messages} messages", inline=False)
        embed.add_field(name="Username", value=f"**Query:** {query}", inline=False)
        embed.set_timestamp()
        return embed

    def _create_progress_image(self, current, total, width=400, height=40):
        progress = current / total
        image = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(image)
        draw.rectangle([0, 0, width, height], outline='black', width=2)
        draw.rectangle([0, 0, int(width * progress), height], fill='green')
        image_path = f"progress_{current}_{total}.png"
        image.save(image_path)
        return image_path

    async def perform_deep_dive(self, username, ctx, client=None):
        if client is None:
            client = self.bot

        search_functions = [self.search_discord]
        for search_function in search_functions:
            platform_name = self.get_platform_name(search_functions.index(search_function))
            await ctx.send(f"Performing a deep dive on {username}... (Searching {platform_name})", ephemeral=True)
            try:
                result = await search_function(username, client, ctx)
                db_path = await self.config.db_path()
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Result (platform, result) VALUES (?, ?)", (platform_name, result))
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"Error performing search function {platform_name}: {e}")

    def get_platform_name(self, index):
        if index == 0:
            return "Discord"
        else:
            return "Unknown"

    async def search_discord(self, query, client, ctx):
        guilds = client.guilds
        found_users = []
        messages = []
        message_count = 0
        total_message_length = 0
        total_messages = 0
        channel_activity = defaultdict(int)
        mention_activity = defaultdict(int)
        time_of_day_activity = [0] * 24
        tfidf = TfIdf()

        checked_servers = 0
        total_servers = len(guilds)

        for guild in guilds:
            checked_servers += 1
            progress_image_path = self._create_progress_image(checked_servers, total_servers)
            await ctx.send(
                embed=self._create_progress_embed(guild.name, checked_servers, total_servers, progress_image_path, message_count, total_messages, query),
                ephemeral=True
            )

            try:
                members = await guild.fetch_members(limit=None).flatten()
                users = [member for member in members if query.lower() in (member.name.lower(), member.display_name.lower(), member.id)]

                if not users:
                    continue

                for user in users:
                    found_users.append(f"{user} in guild {guild.name}")

                    user_messages = await self.fetch_user_messages(guild, user.id)

                    if user_messages:
                        messages.extend(user_messages)
                        message_count += len(user_messages)
                        total_messages += len(user_messages)
                        total_message_length += sum(len(msg['content']) for msg in user_messages)

                        for msg in user_messages:
                            channel_activity[msg['channel']] += 1
                            for mention in msg['mentions']:
                                mention_activity[mention] += 1
                            time_of_day_activity[msg['created_at'].hour] += 1
                            tfidf.add_document(msg['content'])

                            progress_image_path = self._create_progress_image(checked_servers, total_servers)
                            await ctx.send(
                                embed=self._create_progress_embed(guild.name, checked_servers, total_servers, progress_image_path, len(user_messages), total_messages, query),
                                ephemeral=True
                            )
            except Exception as e:
                print(f"Error searching in guild {guild.name}: {e}")
                continue

        if found_users and messages:
            trustworthiness = self.evaluate_trustworthiness(messages)
            intent_summary = self.analyze_intent(messages)
            sentiment_summary = self.analyze_sentiment(messages)
            top_words = self.get_top_words(tfidf)
            avg_message_length = round(total_message_length / message_count, 2)
            most_active_channels = self.get_top_entries(channel_activity, 5)
            most_mentioned_users = self.get_top_entries(mention_activity, 5)
            time_of_day_summary = self.get_time_of_day_summary(time_of_day_activity)

            return f"{', '.join(found_users)}\n\nTrustworthiness: {trustworthiness}\n\nIntent Summary: {intent_summary}\n\nSentiment Summary: {sentiment_summary}\n\nTop Words and Phrases: {top_words}\n\nAverage Message Length: {avg_message_length}\n\nMost Active Channels: {most_active_channels}\n\nMost Mentioned Users: {most_mentioned_users}\n\nActivity by Time of Day: {time_of_day_summary}"
        elif found_users:
            return f"{', '.join(found_users)}\n\nNo messages found for this user."
        else:
            return "No Discord user found with that query"

    async def fetch_user_messages(self, guild, user_id):
        messages = []
        channels = [channel for channel in guild.channels if isinstance(channel, discord.TextChannel)]

        for channel in channels:
            try:
                async for msg in channel.history(limit=100):
                    if msg.author.id == user_id:
                        messages.append({
                            'content': msg.content,
                            'created_at': msg.created_at,
                            'channel': channel.name,
                            'mentions': [mention.name for mention in msg.mentions]
                        })
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Error fetching messages in {channel.name}: {e}")
                continue

        return messages

    def evaluate_trustworthiness(self, messages):
        if not messages:
            return "Not enough data"

        positive_keywords = ['thanks', 'please', 'help', 'support']
        negative_keywords = ['spam', 'scam', 'abuse', 'hate']

        positive_score = sum(1 for msg in messages if any(keyword in msg['content'].lower() for keyword in positive_keywords))
        negative_score = sum(1 for msg in messages if any(keyword in msg['content'].lower() for keyword in negative_keywords))

        total_messages = len(messages)
        positive_ratio = positive_score / total_messages
        negative_ratio = negative_score / total_messages

        if negative_ratio > 0.1:
            return "Untrustworthy"
        elif positive_ratio > 0.1:
            return "Trustworthy"
        else:
            return "Neutral"

    def analyze_sentiment(self, messages):
        if not messages:
            return "Not enough data"

        sentiment_results = [TextBlob(msg['content']).sentiment.polarity for msg in messages]
        average_score = sum(sentiment_results) / len(sentiment_results)

        if average_score > 0:
            return "Overall Positive"
        elif average_score < 0:
            return "Overall Negative"
        else:
            return "Neutral"

    def analyze_intent(self, messages):
        if not messages:
            return "Not enough data"

        intent_keywords = {
            'seeking_help': ['help', 'support', 'assist', 'issue', 'problem'],
            'offering_help': ['assist', 'help', 'support', 'aid', 'offer'],
            'promotion': ['check out', 'subscribe', 'follow', 'buy', 'join'],
            'casual': ['hello', 'hi', 'hey', 'lol', 'haha']
        }

        intents = defaultdict(int)
        for msg in messages:
            for intent, keywords in intent_keywords.items():
                if any(keyword in msg['content'].lower() for keyword in keywords):
                    intents[intent] += 1

        return "\n".join([f"{intent}: {count} messages" for intent, count in intents.items()])

    def get_top_words(self, tfidf):
        return ", ".join(term for term, _ in tfidf.items() if _ > 0.1)

    def get_top_entries(self, dictionary, limit):
        return ", ".join([f"{key}: {value}" for key, value in Counter(dictionary).most_common(limit)])

    def get_time_of_day_summary(self, activity):
        return "\n".join([f"{hour}:00 - {hour + 1}:00: {count}" for hour, count in enumerate(activity)])

def setup(bot: Red):
    bot.add_cog(DeepDive(bot))
