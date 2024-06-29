import discord
from redbot.core import commands, Config

class ServerBlocker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567891)
        default_global = {
            "blocked_servers": []
        }
        self.config.register_global(**default_global)

    @commands.is_owner()
    @commands.group()
    async def serverblock(self, ctx):
        """Manage blocked servers."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @serverblock.command()
    async def add(self, ctx, server_id: int, *, reason: str):
        """Add a server to the blocklist with a reason."""
        async with self.config.blocked_servers() as blocked_servers:
            if server_id not in blocked_servers:
                blocked_servers.append({"id": server_id, "reason": reason})
                guild = self.bot.get_guild(server_id)
                if guild:
                    owner = guild.owner
                    embed = discord.Embed(
                        title="Server Blocked",
                        description=f"Server with ID {server_id} has been added to the blocklist.",
                        color=discord.Color.red()
                    )
                    embed.add_field(name="Server Name", value=guild.name, inline=False)
                    embed.add_field(name="Server Owner", value=f"{owner} ({owner.id})", inline=False)
                    embed.add_field(name="Reason", value=reason, inline=False)
                    await ctx.send(embed=embed)
                else:
                    await ctx.send(f"Server with ID {server_id} has been added to the blocklist, but the server is not currently in the bot's cache.")
            else:
                await ctx.send(f"Server with ID {server_id} is already in the blocklist.")

    @serverblock.command()
    async def remove(self, ctx, server_id: int):
        """Remove a server from the blocklist."""
        async with self.config.blocked_servers() as blocked_servers:
            server = next((s for s in blocked_servers if s["id"] == server_id), None)
            if server:
                blocked_servers.remove(server)
                embed = discord.Embed(
                    title="Server Unblocked",
                    description=f"Server with ID {server_id} has been removed from the blocklist.",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"Server with ID {server_id} is not in the blocklist.")

    @serverblock.command()
    async def list(self, ctx):
        """List all blocked servers."""
        blocked_servers = await self.config.blocked_servers()
        if not blocked_servers:
            await ctx.send("No servers are currently blocked.")
        else:
            embed = discord.Embed(
                title="Blocked Servers",
                description="List of all blocked servers:",
                color=discord.Color.red()
            )
            for server in blocked_servers:
                embed.add_field(name=f"Server ID: {server['id']}", value=f"Reason: {server['reason']}", inline=False)
            await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        """Prevent the bot from joining blocked servers."""
        blocked_servers = await self.config.blocked_servers()
        if any(server["id"] == guild.id for server in blocked_servers):
            await guild.leave()
            print(f"Left blocked server: {guild.name} (ID: {guild.id})")
