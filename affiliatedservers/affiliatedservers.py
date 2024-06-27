import discord
from redbot.core import commands, Config

class AffiliatedServers(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_global = {
            "affiliated_servers": []
        }
        self.config.register_global(**default_global)

    @commands.is_owner()
    @commands.group()
    async def affiliate(self, ctx):
        """Manage affiliated servers."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @affiliate.command()
    async def add(self, ctx, message: str, name: str, invite: str):
        """Add a new affiliated server."""
        async with self.config.affiliated_servers() as affiliated_servers:
            affiliated_servers.append({
                "message": message,
                "name": name,
                "invite": invite
            })
        await ctx.send(f"Affiliated server '{name}' added successfully!")

    @affiliate.command()
    async def list(self, ctx):
        """List all affiliated servers."""
        affiliated_servers = await self.config.affiliated_servers()
        if not affiliated_servers:
            await ctx.send("No affiliated servers found.")
            return

        parent_embed = discord.Embed(
            title="Affiliated Servers",
            description="The servers listed below are affiliated with FuturoBot",
            color=discord.Color.blue()
        )

        for server in affiliated_servers:
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
        await self.config.affiliated_servers.set([])
        await ctx.send("All affiliated servers have been cleared.")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Event listener that triggers when a new member joins a server."""
        affiliated_servers = await self.config.affiliated_servers()
        if not affiliated_servers:
            return  # No affiliated servers to send

        initial_message = "The servers listed below are affiliated with FuturoBot"

        try:
            await member.send(initial_message)
            for server in affiliated_servers:
                embed = discord.Embed(
                    title=server["name"],
                    description=server["message"],
                    color=discord.Color.green()
                )
                embed.add_field(name="Invite", value=server["invite"])
                await member.send(embed=embed)
        except discord.Forbidden:
            print(f"Could not send DM to the new member: {member.name}")
