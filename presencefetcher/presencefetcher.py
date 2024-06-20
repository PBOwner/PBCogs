import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
from datetime import datetime, timedelta

class PresenceFetcher(commands.Cog):
    """Cog to fetch and track user presence information."""

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
    async def shared(self, ctx, user: discord.User):
        """Fetch and display the user's status across servers shared with the bot."""
        shared_guilds = [guild for guild in self.bot.guilds if guild.get_member(user.id)]
        embed = discord.Embed(
            title=f"Status of {user.display_name} across shared servers",
            color=discord.Color.blue()
        )

        if shared_guilds:
            for guild in shared_guilds:
                member = guild.get_member(user.id)
                status_type = self.get_status_type(member.status)
                custom_status = next((activity for activity in member.activities if isinstance(activity, discord.CustomActivity)), None)
                status_text = status_type
                if custom_status:
                    status_text += f"\nCustom Status: {custom_status.name}"
                embed.add_field(name=guild.name, value=status_text, inline=False)
        else:
            embed.description = "No shared servers found."

        await ctx.send(embed=embed)

    @fetch.command()
    async def past(self, ctx, user: discord.User):
        """Fetch and display the user's past statuses."""
        presence_changes = await self.config.guild(ctx.guild).presence_changes()
        changes = presence_changes.get(str(user.id), [])

        embed = discord.Embed(
            title=f"Past Statuses of {user.display_name}",
            color=discord.Color.purple()
        )

        if changes:
            for change in changes:
                timestamp = datetime.fromisoformat(change["timestamp"])
                status = change["status"]
                custom_status = change.get("custom_status", "No custom status")
                embed.add_field(name=timestamp.strftime("%Y-%m-%d %H:%M:%S"), value=f"Status: {status}\nCustom Status: {custom_status}", inline=False)
        else:
            embed.description = "No past statuses recorded."

        await ctx.send(embed=embed)

    @fetch.command()
    async def allusers(self, ctx):
        """Fetch and display the statuses of all users in the server."""
        members = ctx.guild.members
        embed = discord.Embed(
            title=f"Statuses of All Users in {ctx.guild.name}",
            color=discord.Color.green()
        )

        for member in members:
            status_type = self.get_status_type(member.status)
            custom_status = next((activity for activity in member.activities if isinstance(activity, discord.CustomActivity)), None)
            status_text = status_type
            if custom_status:
                status_text += f"\nCustom Status: {custom_status.name}"
            embed.add_field(name=member.display_name, value=status_text, inline=True)

        await ctx.send(embed=embed)

    def get_status_type(self, status):
        """Helper method to get the status type as a string."""
        if status == discord.Status.online:
            return "Online"
        elif status == discord.Status.offline:
            return "Offline"
        elif status == discord.Status.idle:
            return "Idle"
        elif status == discord.Status.dnd:
            return "Do Not Disturb"
        else:
            return str(status).capitalize()

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        if before.status != after.status or before.activities != after.activities:
            guild = after.guild
            if guild:
                async with self.config.guild(guild).presence_changes() as presence_changes:
                    changes = presence_changes.get(str(after.id), [])
                    custom_status = next((activity for activity in after.activities if isinstance(activity, discord.CustomActivity)), None)
                    changes.append({
                        "timestamp": datetime.utcnow().isoformat(),
                        "status": self.get_status_type(after.status),
                        "custom_status": custom_status.name if custom_status else "No custom status"
                    })
                    # Keep only the changes from the last 100 days
                    changes = [change for change in changes if datetime.fromisoformat(change["timestamp"]) > datetime.utcnow() - timedelta(days=100)]
                    presence_changes[str(after.id)] = changes

def setup(bot: Red):
    bot.add_cog(PresenceFetcher(bot))
