import discord
from redbot.core import commands, Config
import uuid

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
        new_affiliate = {
            "id": str(uuid.uuid4()),
            "message": message,
            "name": name,
            "invite": invite
        }
        async with self.config.affiliated_servers() as affiliated_servers:
            affiliated_servers.append(new_affiliate)
        await ctx.send(f"Affiliated server '{name}' added successfully with ID {new_affiliate['id']}!")

    @affiliate.command()
    async def list(self, ctx):
        """List all affiliated servers."""
        affiliated_servers = await self.config.affiliated_servers()
        if not affiliated_servers:
            await ctx.send("No affiliated servers found.")
            return

        for server in affiliated_servers:
            embed = discord.Embed(
                title=server["name"],
                description=server["message"],
                color=discord.Color.green()
            )
            embed.add_field(name="Invite", value=server["invite"])
            embed.set_footer(text=f"ID: {server['id']}")
            await ctx.send(embed=embed)

    @affiliate.command()
    async def view(self, ctx, affiliate_id: str):
        """View a specific affiliated server by ID."""
        affiliated_servers = await self.config.affiliated_servers()
        server = next((s for s in affiliated_servers if s["id"] == affiliate_id), None)
        if not server:
            await ctx.send(f"No affiliated server found with ID {affiliate_id}.")
            return

        embed = discord.Embed(
            title=server["name"],
            description=server["message"],
            color=discord.Color.green()
        )
        embed.add_field(name="Invite", value=server["invite"])
        embed.set_footer(text=f"ID: {server['id']}")
        await ctx.send(embed=embed)

    @affiliate.command()
    async def delete(self, ctx, affiliate_id: str):
        """Delete an affiliated server by ID."""
        async with self.config.affiliated_servers() as affiliated_servers:
            server = next((s for s in affiliated_servers if s["id"] == affiliate_id), None)
            if not server:
                await ctx.send(f"No affiliated server found with ID {affiliate_id}.")
                return
            affiliated_servers.remove(server)
        await ctx.send(f"Affiliated server '{server['name']}' deleted successfully!")

    @affiliate.command()
    async def edit(self, ctx, affiliate_id: str, field: str, value: str):
        """Edit a specific field of an affiliated server by ID."""
        async with self.config.affiliated_servers() as affiliated_servers:
            server = next((s for s in affiliated_servers if s["id"] == affiliate_id), None)
            if not server:
                await ctx.send(f"No affiliated server found with ID {affiliate_id}.")
                return
            if field not in server:
                await ctx.send(f"Invalid field '{field}'. Valid fields are: message, name, invite.")
                return
            server[field] = value
        await ctx.send(f"Affiliated server '{server['name']}' updated successfully!")

    @affiliate.command()
    async def move(self, ctx, affiliate_id: str, position: int):
        """Move an affiliated server to a different position."""
        async with self.config.affiliated_servers() as affiliated_servers:
            server_index = next((i for i, s in enumerate(affiliated_servers) if s["id"] == affiliate_id), None)
            if server_index is None:
                await ctx.send(f"No affiliated server found with ID {affiliate_id}.")
                return

            # Ensure the position is within valid range
            if position < 0 or position >= len(affiliated_servers):
                await ctx.send(f"Invalid position. Must be between 0 and {len(affiliated_servers) - 1}.")
                return

            server = affiliated_servers.pop(server_index)
            affiliated_servers.insert(position, server)
        await ctx.send(f"Affiliated server '{server['name']}' moved to position {position} successfully!")

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
