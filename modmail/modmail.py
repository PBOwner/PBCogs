from redbot.core import commands, Config
from redbot.core.bot import Red
import discord
import logging
import datetime
import asyncio

class Thread:
    def __init__(self, member_id: int, messages: list, created_at: int):
        self.member_id = member_id
        self.messages = messages
        self.created_at = created_at

    def json(self):
        return {
            "member_id": self.member_id,
            "messages": self.messages,
            "created_at": self.created_at
        }

    @classmethod
    def from_json(cls, data: dict):
        return cls(data['member_id'], data['messages'], data['created_at'])

class Modmail(commands.Cog):
    """Simple modmail cog"""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=2480948239048209, force_registration=True)
        self.logger = logging.getLogger('red.modmail')
        default_guild = {
            "mod_channel_id": None,
            "threads": []
        }
        self.config.register_guild(**default_guild)
        default_global = {
            "user_guild_mapping": {}
        }
        self.config.register_global(**default_global)

    async def init_threads(self, guild_id: int):
        await self.config.guild_from_id(guild_id).threads.set([])

    async def create_user_thread(self, guild_id: int, member: discord.Member, initial_message: discord.Message):
        async with self.config.guild_from_id(guild_id).threads() as threads:
            thread = Thread(member.id, [initial_message.id], int(datetime.datetime.utcnow().timestamp()))
            threads.append(thread.json())

    async def get_user_thread(self, guild_id: int, member: discord.Member):
        threads = await self.config.guild_from_id(guild_id).threads()
        for thread in threads:
            if thread['member_id'] == member.id:
                return Thread.from_json(thread)
        return None

    @commands.guild_only()
    @commands.command()
    async def threads(self, ctx: commands.Context):
        """Show all current modmail threads."""
        guild_id = ctx.guild.id
        threads = await self.config.guild_from_id(guild_id).threads()
        embed = discord.Embed(title="ModMail Threads")
        for thread_json in threads:
            thread = Thread.from_json(thread_json)
            member = self.bot.get_user(thread.member_id)
            if member:
                embed.add_field(name=f"{member.name} ({member.id})", value=f"Created at: {datetime.datetime.fromtimestamp(thread.created_at)}")
        await ctx.channel.send(embed=embed)

    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @commands.command()
    async def setmodchannel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the modmail channel where notifications will be sent."""
        await self.config.guild(ctx.guild).mod_channel_id.set(channel.id)
        await ctx.send(f"Modmail channel set to {channel.mention}")

    @commands.admin_or_permissions(manage_guild=True)
    @commands.command()
    async def setmodmailguild(self, ctx: commands.Context):
       """Set the server for modmail configuration to the guild where the command is run."""
       guild = ctx.guild
    
    # Ensure that the user_guild_mapping is initialized
       user_guild_mapping = await self.config.user(ctx.author).global_user.user_guild_mapping()
       if not user_guild_mapping:
           user_guild_mapping = {}

       user_guild_mapping[str(ctx.author.id)] = guild.id
       await self.config.user(ctx.author).global_user.user_guild_mapping.set(user_guild_mapping)
    
       await ctx.send(f"Modmail server set to {guild.name} (ID: {guild.id})")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is not None:
            return
        if message.author.bot:
            return

        guild_id = await self.get_guild_id_for_modmail(message.author.id)
        if not guild_id:
            guild_id = await self.prompt_user_for_guild(message.author)

        if not guild_id:
            return

        threads = await self.config.guild_from_id(guild_id).threads()
        if not threads:
            await self.init_threads(guild_id)
        
        user_thread = await self.get_user_thread(guild_id, message.author)
        if not user_thread:
            await self.create_user_thread(guild_id, message.author, message)
            await message.add_reaction("✅")
            await message.channel.send(embed=discord.Embed(title="Thread Created", description="A staff member will be with you shortly."))
        else:
            await message.add_reaction("✅")
            user_thread.messages.append(message.id)
            async with self.config.guild_from_id(guild_id).threads() as threads:
                for i, thread in enumerate(threads):
                    if thread['member_id'] == message.author.id:
                        threads[i] = user_thread.json()
                        break

            mod_channel_id = await self.config.guild_from_id(guild_id).mod_channel_id()
            mod_channel = self.bot.get_channel(mod_channel_id)
            if mod_channel:
                embed = discord.Embed(title="New ModMail Message", description=message.content, timestamp=message.created_at)
                embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
                await mod_channel.send(embed=embed)

    async def get_guild_id_for_modmail(self, user_id: int):
        global_config = await self.config.user_from_id(user_id).global_user()
        return global_config.get('user_guild_mapping', {}).get(str(user_id))

    async def prompt_user_for_guild(self, user: discord.User):
        guilds = [guild for guild in self.bot.guilds if guild.get_member(user.id) is not None]
        guild_list = "\n".join([f"{i+1}. {guild.name} (ID: {guild.id})" for i, guild in enumerate(guilds)])
        await user.send(f"Which server is this for? Please reply with the number:\n{guild_list}")

        def check(m):
            return m.author == user and isinstance(m.channel, discord.DMChannel) and m.content.isdigit()

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=60)
            guild_index = int(msg.content) - 1
            if guild_index < 0 or guild_index >= len(guilds):
                await user.send("Invalid number. Please try the command again.")
                return None

            selected_guild = guilds[guild_index]
            global_config = await self.config.user(user).global_user.get_raw('user_guild_mapping', default={})
            
            global_config[str(user.id)] = selected_guild.id
            await self.config.user(user).global_user.set_raw('user_guild_mapping', value=global_config)
            
            await user.send(f"Modmail server set to {selected_guild.name} (ID: {selected_guild.id})")
            return selected_guild.id

        except asyncio.TimeoutError:
            await user.send("You took too long to respond. Please try the command again.")
            return None
