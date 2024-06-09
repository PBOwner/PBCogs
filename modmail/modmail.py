from redbot.core import commands, Config
from redbot.core.bot import Red
import discord
import logging
import datetime
import asyncio

class Thread:
    def __init__(self, member_id: int, messages: list, created_at: int, thread_number: int):
        self.member_id = member_id
        self.messages = messages
        self.created_at = created_at
        self.thread_number = thread_number

    def json(self):
        return {
            "member_id": self.member_id,
            "messages": self.messages,
            "created_at": self.created_at,
            "thread_number": self.thread_number
        }

    @classmethod
    def from_json(cls, data: dict):
        return cls(data['member_id'], data['messages'], data['created_at'], data['thread_number'])

class Modmail(commands.Cog):
    """Simple modmail cog"""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=2480948239048209, force_registration=True)
        self.logger = logging.getLogger('red.modmail')
        default_guild = {
            "mod_channel_id": None,
            "modmail_category_id": None,
            "channel_name_format": "modmail-{username}-{userid}",
            "modmail_role_id": None,
            "threads": [],
            "thread_count": 0
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
            async with self.config.guild_from_id(guild_id).thread_count() as thread_count:
                thread_count += 1
                thread_number = thread_count
            thread = Thread(member.id, [initial_message.id], int(datetime.datetime.utcnow().timestamp()), thread_number)
            threads.append(thread.json())

    async def get_user_thread(self, guild_id: int, member: discord.Member):
        threads = await self.config.guild_from_id(guild_id).threads()
        for thread in threads:
            if thread['member_id'] == member.id:
                return Thread.from_json(thread)
        return None

    def has_modmail_role():
        async def predicate(ctx: commands.Context):
            modmail_role_id = await ctx.bot.get_cog('Modmail').config.guild(ctx.guild).modmail_role_id()
            if modmail_role_id:
                role = discord.utils.get(ctx.guild.roles, id=modmail_role_id)
                if role in ctx.author.roles:
                    return True
            return False
        return commands.check(predicate)

    @commands.guild_only()
    @commands.command()
    @commands.is_owner()
    async def setmodchannel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the modmail channel where notifications will be sent."""
        await self.config.guild(ctx.guild).mod_channel_id.set(channel.id)
        await ctx.send(f"Modmail channel set to {channel.mention}")

    @commands.guild_only()
    @commands.command()
    @commands.is_owner()
    async def setmodmailguild(self, ctx: commands.Context):
        """Set the server for modmail configuration to the guild where the command is run."""
        guild = ctx.guild

        # Ensure that the user_guild_mapping is initialized
        user_guild_mapping = await self.config.user(ctx.author).user_guild_mapping()
        if user_guild_mapping is None:
            user_guild_mapping = {}

        user_guild_mapping[str(ctx.author.id)] = guild.id
        await self.config.user(ctx.author).user_guild_mapping.set(user_guild_mapping)

        await ctx.send(f"Modmail server set to {guild.name} (ID: {guild.id})")

    @commands.guild_only()
    @commands.command()
    @commands.is_owner()
    async def setmodmailrole(self, ctx: commands.Context, role: discord.Role):
        """Set the modmail role which can run modmail commands."""
        await self.config.guild(ctx.guild).modmail_role_id.set(role.id)
        await ctx.send(f"Modmail role set to {role.name}")

    @commands.guild_only()
    @commands.command()
    @has_modmail_role()
    async def threads(self, ctx: commands.Context):
        """Show all current modmail threads."""
        guild_id = ctx.guild.id
        threads = await self.config.guild_from_id(guild_id).threads()
        embed = discord.Embed(title="ModMail Threads")
        for thread_json in threads:
            thread = Thread.from_json(thread_json)
            member = self.bot.get_user(thread.member_id)
            if member:
                embed.add_field(name=f"{member.name} ({member.id})", value=f"Created at: {datetime.datetime.fromtimestamp(thread.created_at)}\nThread number: {thread.thread_number}")
        await ctx.channel.send(embed=embed)

    @commands.guild_only()
    @commands.command()
    @has_modmail_role()
    async def setmodmailcategory(self, ctx: commands.Context, category: discord.CategoryChannel):
        """Set the category where modmail channels will be created."""
        await self.config.guild(ctx.guild).modmail_category_id.set(category.id)
        await ctx.send(f"Modmail category set to {category.name}")

    @commands.guild_only()
    @commands.command()
    @has_modmail_role()
    async def setformat(self, ctx: commands.Context, *, format: str):
        """Set the format for modmail channel names."""
        await self.config.guild(ctx.guild).channel_name_format.set(format)
        await ctx.send(f"Modmail channel name format set to `{format}`")

    @commands.guild_only()
    @commands.command()
    @has_modmail_role()
    async def rename(self, ctx: commands.Context, *, new_name: str):
        """Rename the modmail thread channel."""
        thread = await self.get_thread_by_channel(ctx.guild.id, ctx.channel.id)
        if thread:
            await ctx.channel.edit(name=new_name)
            await ctx.send(f"Modmail channel name changed to `{new_name}`")
        else:
            await ctx.send("This command can only be used in a modmail thread channel.")

    @commands.guild_only()
    @commands.command()
    @has_modmail_role()
    async def move(self, ctx: commands.Context, *, category_name_or_id: str):
        """Move the modmail thread channel to a different category."""
        thread = await self.get_thread_by_channel(ctx.guild.id, ctx.channel.id)
        if thread:
            category = discord.utils.get(ctx.guild.categories, name=category_name_or_id) or \
                       discord.utils.get(ctx.guild.categories, id=int(category_name_or_id))
            if category:
                await ctx.channel.edit(category=category)
                await ctx.send(f"Modmail channel moved to `{category.name}` category")
            else:
                await ctx.send("Category not found. Please provide a valid category name or ID.")
        else:
            await ctx.send("This command can only be used in a modmail thread channel.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None:  # Check if the message is from a DM
            if message.author.bot:
                return

            guild_id = await self.get_guild_id_for_modmail(message.author.id)
            if not guild_id:
                guild_id = await self.prompt_user_for_guild(message.author)

            if not guild_id:
                return

            user_thread = await self.get_user_thread(guild_id, message.author)
            if not user_thread:
                await self.create_user_thread(guild_id, message.author, message)
                await self.create_modmail_channel(guild_id, message.author, message)
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

    async def create_modmail_channel(self, guild_id: int, user: discord.User, message: discord.Message):
        guild = self.bot.get_guild(guild_id)
        category_id = await self.config.guild(guild).modmail_category_id()
        if category_id:
            category = discord.utils.get(guild.categories, id=category_id)
            if category:
                format = await self.config.guild(guild).channel_name_format()
                thread_number = await self.get_thread_number(guild_id, user.id)
                channel_name = format.format(
                    username=user.name,
                    userid=user.id,
                    threadnumber=thread_number,
                    shortdate=datetime.datetime.utcnow().strftime("%Y%m%d")
                )
                channel = await guild.create_text_channel(name=channel_name, category=category)
                await channel.send(embed=discord.Embed(title="New ModMail Thread", description=f"User: {user.name} ({user.id})"))
                return channel

    async def get_thread_number(self, guild_id: int, user_id: int):
        threads = await self.config.guild_from_id(guild_id).threads()
        for thread in threads:
            if thread['member_id'] == user_id:
                return thread['thread_number']
        return 0

    async def get_thread_by_channel(self, guild_id: int, channel_id: int):
        threads = await self.config.guild_from_id(guild_id).threads()
        for thread in threads:
            if thread['channel_id'] == channel_id:
                return thread
        return None

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
            global_config = await self.config.user(user).global_user()

            user_guild_mapping = global_config.get('user_guild_mapping', {})
            user_guild_mapping[str(user.id)] = selected_guild.id
            await self.config.user(user).global_user.set_raw('user_guild_mapping', value=user_guild_mapping)

            await user.send(f"Modmail server set to {selected_guild.name} (ID: {selected_guild.id})")
            return selected_guild.id

        except asyncio.TimeoutError:
            await user.send("You took too long to respond. Please try the command again.")
            return None

def setup(bot: Red):
    bot.add_cog(Modmail(bot))
