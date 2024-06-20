import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
from datetime import datetime, timedelta

class PresenceFetcher(commands.Cog):
    """Cog to fetch presence information using the Presence Intent."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        default_guild = {
            "presence_changes": {}
        }
        self.config.register_guild(**default_guild)

    @commands.group(invoke_without_command=True)
    async def fetch(self, ctx):
        """Base command for fetching presence information."""
        await ctx.send_help(ctx.command)

    @fetch.command()
    async def users(self, ctx):
        """Fetch and display the presence information for all users (excluding bots) in the server."""
        await self.fetch_presence(ctx, lambda member: not member.bot)

    @fetch.command()
    async def bots(self, ctx):
        """Fetch and display the presence information for all bots in the server."""
        await self.fetch_presence(ctx, lambda member: member.bot)

    @fetch.command()
    async def all(self, ctx):
        """Fetch and display the presence information for all members in the server."""
        await self.fetch_presence(ctx, lambda member: True)

    @fetch.command()
    async def online(self, ctx):
        """Fetch and display the presence information for all online members in the server."""
        await self.fetch_presence(ctx, lambda member: member.status == discord.Status.online)

    @fetch.command()
    async def offline(self, ctx):
        """Fetch and display the presence information for all offline members in the server."""
        await self.fetch_presence(ctx, lambda member: member.status == discord.Status.offline)

    @fetch.command()
    async def dnd(self, ctx):
        """Fetch and display the presence information for all members with Do Not Disturb status in the server."""
        await self.fetch_presence(ctx, lambda member: member.status == discord.Status.dnd)

    @fetch.command()
    async def idle(self, ctx):
        """Fetch and display the presence information for all idle members in the server."""
        await self.fetch_presence(ctx, lambda member: member.status == discord.Status.idle)

    @fetch.command()
    async def humans(self, ctx):
        """Fetch and display the presence information for all human users (excluding bots) in the server."""
        await self.fetch_presence(ctx, lambda member: not member.bot)

    @fetch.command()
    async def shared(self, ctx, user: discord.User):
        """Fetch and display the servers a specified user shares with the bot and their custom statuses."""
        shared_guilds = [guild for guild in self.bot.guilds if guild.get_member(user.id)]
        embed = discord.Embed(
            title=f"Servers shared with {user.display_name}",
            color=discord.Color.blue()
        )

        if shared_guilds:
            for guild in shared_guilds:
                member = guild.get_member(user.id)
                custom_status = next((activity for activity in member.activities if isinstance(activity, discord.CustomActivity)), None)
                status_text = custom_status.name if custom_status else "No custom status"
                embed.add_field(name=guild.name, value=status_text, inline=False)
        else:
            embed.description = "No shared servers found."

        await ctx.send(embed=embed)

    @fetch.command()
    async def previous(self, ctx, member: discord.Member):
        """Fetch and display the presence changes of a member in the last 100 days."""
        presence_changes = await self.config.guild(ctx.guild).presence_changes()
        changes = presence_changes.get(str(member.id), [])

        embed = discord.Embed(
            title=f"Presence Changes for {member.display_name} in the Last 100 Days",
            color=discord.Color.purple()
        )

        if changes:
            for change in changes:
                timestamp = datetime.fromisoformat(change["timestamp"])
                status = change["status"]
                embed.add_field(name=timestamp.strftime("%Y-%m-%d %H:%M:%S"), value=status, inline=False)
        else:
            embed.description = "No presence changes recorded."

        await ctx.send(embed=embed)

    async def fetch_presence(self, ctx, predicate):
        """Helper method to fetch and display presence information based on a predicate."""
        try:
            members = []
            async for member in ctx.guild.fetch_members(limit=None):
                members.append(member)

            embed = discord.Embed(
                title=f"Presence Information for Members in {ctx.guild.name}",
                color=discord.Color.green()
            )

            for member in filter(predicate, members):
                status_type = member.status.name.capitalize()  # Display status (Online, Offline, Idle, Dnd)
                if status_type.lower() == 'dnd':
                    status_type = 'DND'
                custom_status = next((activity for activity in member.activities if isinstance(activity, discord.CustomActivity)), None)
                status_text = status_type
                if custom_status:
                    status_text += f"\nCustom Status: {custom_status.name}"  # Add custom status if it exists
                embed.add_field(name=member.display_name, value=status_text, inline=True)

            await ctx.send(embed=embed)

        except discord.HTTPException as e:
            await ctx.send(f"Failed to fetch presence information: {e}")

    @commands.Cog.listener()
    async def on_presence_update(self, before, after):
        if before.status != after.status:
            guild = after.guild
            if guild:
                async with self.config.guild(guild).presence_changes() as presence_changes:
                    changes = presence_changes.get(str(after.id), [])
                    changes.append({
                        "timestamp": datetime.utcnow().isoformat(),
                        "status": str(after.status)
                    })
                    # Keep only the changes from the last 100 days
                    changes = [change for change in changes if datetime.fromisoformat(change["timestamp"]) > datetime.utcnow() - timedelta(days=100)]
                    presence_changes[str(after.id)] = changes

def setup(bot: Red):
    bot.add_cog(PresenceFetcher(bot))
