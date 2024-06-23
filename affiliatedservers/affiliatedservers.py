import discord
from redbot.core import commands

class AffiliatedServers(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.affiliated_servers = []

    @commands.is_owner()
    @commands.group()
    async def affiliate(self, ctx):
        """Manage affiliated servers."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @affiliate.command()
    async def add(self, ctx, message: str, name: str, invite: str):
        """Add a new affiliated server."""
        self.affiliated_servers.append({
            "message": message,
            "name": name,
            "invite": invite
        })
        await ctx.send(f"Affiliated server '{name}' added successfully!")

    @affiliate.command()
    async def list(self, ctx):
        """List all affiliated servers."""
        if not self.affiliated_servers:
            await ctx.send("No affiliated servers found.")
            return

        parent_embed = discord.Embed(
            title="Affiliated Servers",
            description="The servers listed below are affiliated with FuturoBot",
            color=discord.Color.blue()
        )

        for server in self.affiliated_servers:
            embed = discord.Embed(
                title=server["name"],
                description=server["message"],
                color=discord.Color.green()
            )
            embed.add_field(name="Invite", value=server["invite"])
            await ctx.send(embed=embed)

        await ctx.send(embed=parent_embed)

    @affiliate.command()
    async def clear(self, ctx):
        """Clear all affiliated servers."""
        self.affiliated_servers.clear()
        await ctx.send("All affiliated servers have been cleared.")

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        """Event listener that triggers when the bot joins a server."""
        if not self.affiliated_servers:
            return  # No affiliated servers to send

        parent_embed = discord.Embed(
            title="Affiliated Servers",
            description="The servers listed below are affiliated with FuturoBot",
            color=discord.Color.blue()
        )

        owner = guild.owner
        if owner:
            try:
                await owner.send(embed=parent_embed)
                for server in self.affiliated_servers:
                    embed = discord.Embed(
                        title=server["name"],
                        description=server["message"],
                        color=discord.Color.green()
                    )
                    embed.add_field(name="Invite", value=server["invite"])
                    await owner.send(embed=embed)
            except discord.Forbidden:
                print(f"Could not send DM to the owner of the guild: {guild.name}")

def setup(bot):
    bot.add_cog(AffiliatedServers(bot))
