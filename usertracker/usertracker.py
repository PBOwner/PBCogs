import discord
from redbot.core import commands
from redbot.core.bot import Red
import aiosqlite
import datetime

class UserTracker(commands.Cog):
    """Cog to track user joins and leaves."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.bot.loop.create_task(self.initialize_existing_members())

    async def initialize_existing_members(self):
        await self.bot.wait_until_ready()
        async with aiosqlite.connect("user_tracker.db") as db:
            await db.execute("CREATE TABLE IF NOT EXISTS joins (user_id INTEGER, join_time TEXT, guild_id INTEGER)")
            await db.execute("CREATE TABLE IF NOT EXISTS leaves (user_id INTEGER, leave_time TEXT, guild_id INTEGER)")
            for guild in self.bot.guilds:
                for member in guild.members:
                    async with db.execute("SELECT 1 FROM joins WHERE user_id = ? AND guild_id = ?", (member.id, guild.id)) as cursor:
                        if not await cursor.fetchone():
                            await db.execute("INSERT INTO joins (user_id, join_time, guild_id) VALUES (?, ?, ?)", (member.id, member.joined_at.isoformat(), guild.id))
            await db.commit()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        async with aiosqlite.connect("user_tracker.db") as db:
            await db.execute("CREATE TABLE IF NOT EXISTS joins (user_id INTEGER, join_time TEXT, guild_id INTEGER)")
            await db.execute("INSERT INTO joins (user_id, join_time, guild_id) VALUES (?, ?, ?)", (member.id, datetime.datetime.utcnow().isoformat(), member.guild.id))
            await db.commit()

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        async with aiosqlite.connect("user_tracker.db") as db:
            await db.execute("CREATE TABLE IF NOT EXISTS leaves (user_id INTEGER, leave_time TEXT, guild_id INTEGER)")
            await db.execute("INSERT INTO leaves (user_id, leave_time, guild_id) VALUES (?, ?, ?)", (member.id, datetime.datetime.utcnow().isoformat(), member.guild.id))
            await db.commit()

    @commands.command()
    async def userlog(self, ctx, user_id: int):
        """Fetch join/leave log for a user by user ID."""
        async with aiosqlite.connect("user_tracker.db") as db:
            await db.execute("CREATE TABLE IF NOT EXISTS joins (user_id INTEGER, join_time TEXT, guild_id INTEGER)")
            await db.execute("CREATE TABLE IF NOT EXISTS leaves (user_id INTEGER, leave_time TEXT, guild_id INTEGER)")
            async with db.execute("SELECT join_time, guild_id FROM joins WHERE user_id = ?", (user_id,)) as cursor:
                joins = await cursor.fetchall()
            async with db.execute("SELECT leave_time, guild_id FROM leaves WHERE user_id = ?", (user_id,)) as cursor:
                leaves = await cursor.fetchall()

        join_times = [(datetime.datetime.fromisoformat(j[0]), j[1]) for j in joins]
        leave_times = [(datetime.datetime.fromisoformat(l[0]), l[1]) for l in leaves]

        join_leave_info = {}
        for join_time, guild_id in join_times:
            guild = self.bot.get_guild(guild_id)
            guild_name = guild.name if guild else "Unknown Guild"
            leave_time = next((l[0] for l in leave_times if l[1] == guild_id and l[0] > join_time), None)
            day_of_week = join_time.strftime('%A')
            if day_of_week not in join_leave_info:
                join_leave_info[day_of_week] = []
            if leave_time:
                join_leave_info[day_of_week].append(f"Guild: {guild_name} - Joined: {join_time}, Left: {leave_time}")
            else:
                join_leave_info[day_of_week].append(f"Guild: {guild_name} - Joined: {join_time}, Still in server")

        embed = discord.Embed(title=f"Join/Leave Log for User ID: {user_id}")
        for day, events in join_leave_info.items():
            embed.add_field(name=day, value="\n".join(events), inline=False)

        await ctx.send(embed=embed)

def setup(bot: Red):
    bot.add_cog(UserTracker(bot))
