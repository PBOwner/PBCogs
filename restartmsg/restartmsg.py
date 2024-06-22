import os
import sys
from redbot.core import commands, Config
import discord

class RestartMsg(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier="restartmsg", force_registration=True)
        self.config.register_global(ignore_servers=[])

    @commands.command(name='warnrestart')
    @commands.is_owner()
    async def warnrestart(self, ctx, *, message: str):
        """Send a message to all Server Owners, except those in the ignore list, and restart the bot."""
        embed = discord.Embed(title="Incoming Restart", description=message, color=discord.Color.red())
        ignore_servers = await self.config.ignore_servers()
        owners_notified = set()  # To track which owners have been notified

        for guild in self.bot.guilds:
            if guild.id in ignore_servers:
                continue

            owner = guild.owner
            if owner and owner.id not in owners_notified:
                try:
                    await owner.send(embed=embed)
                    owners_notified.add(owner.id)
                except Exception as e:
                    print(f"Failed to send message to {owner}: {e}")

        await ctx.send(embed=discord.Embed(title="Restarting", description="Restart message sent to all guild owners. Restarting bot...", color=discord.Color.green()))

        # Restart the bot process
        os.execv(sys.executable, [sys.executable] + sys.argv)

    @commands.command(name='testmsg')
    @commands.is_owner()
    async def testmsg(self, ctx, guild_id: int, *, message: str):
        """Send a test message to a specific Server Owner without restarting the bot."""
        embed = discord.Embed(title="Testing a Restart Warning", description=message, color=discord.Color.red())
        embed.add_field(name="Owner", value=ctx.author.mention, inline=False)

        guild = self.bot.get_guild(guild_id)
        if guild:
            owner = guild.owner
            if owner:
                try:
                    await owner.send(embed=embed)
                    await ctx.send(embed=discord.Embed(title="Message Sent", description=f"Test message sent to the owner of `{guild.name}`.", color=discord.Color.green()))
                except Exception as e:
                    await ctx.send(embed=discord.Embed(title="ErRoR 404", description=f"Failed to send message to {owner}: {e}", color=discord.Color.red()))
        else:
            await ctx.send(embed=discord.Embed(title="ErRoR 404", description=f"Guild with ID {guild_id} not found.", color=discord.Color.red()))

    @commands.command(name='ignoreowner')
    @commands.is_owner()
    async def ignoreowner(self, ctx, guild_id: int):
        """Add a server's owner to the ignore list."""
        ignore_servers = await self.config.ignore_servers()
        guild = self.bot.get_guild(guild_id)
        if guild:
            owner = guild.owner
            if guild_id not in ignore_servers:
                ignore_servers.append(guild_id)
                await self.config.ignore_servers.set(ignore_servers)
                embed = discord.Embed(title="Now Ignoring", color=discord.Color.orange())
                embed.add_field(name="Server Name", value=guild.name, inline=False)
                embed.add_field(name="Server ID", value=guild.id, inline=False)
                embed.add_field(name="Server Owner Name", value=owner.name, inline=False)
                embed.add_field(name="Server Owner ID", value=owner.id, inline=False)
                await ctx.send(embed=embed)
            else:
                await ctx.send(embed=discord.Embed(title="ErRoR 404", description=f"Owner of server with ID {guild_id} is already ignored.", color=discord.Color.red()))
        else:
            await ctx.send(embed=discord.Embed(title="ErRoR 404", description=f"Guild with ID {guild_id} not found.", color=discord.Color.red()))

    @commands.command(name='unignoreowner')
    @commands.is_owner()
    async def unignoreowner(self, ctx, guild_id: int):
        """Remove a server's owner from the ignore list."""
        ignore_servers = await self.config.ignore_servers()
        guild = self.bot.get_guild(guild_id)
        if guild:
            owner = guild.owner
            if guild_id in ignore_servers:
                ignore_servers.remove(guild_id)
                await self.config.ignore_servers.set(ignore_servers)
                embed = discord.Embed(title="No Longer Ignoring", color=discord.Color.green())
                embed.add_field(name="Server Name", value=guild.name, inline=False)
                embed.add_field(name="Server ID", value=guild.id, inline=False)
                embed.add_field(name="Server Owner Name", value=owner.name, inline=False)
                embed.add_field(name="Server Owner ID", value=owner.id, inline=False)
                await ctx.send(embed=embed)
            else:
                await ctx.send(embed=discord.Embed(title="ErRoR 404", description=f"Owner of server with ID {guild_id} is not in the ignore list.", color=discord.Color.red()))
        else:
            await ctx.send(embed=discord.Embed(title="ErRoR 404", description=f"Guild with ID {guild_id} not found.", color=discord.Color.red()))

def setup(bot):
    bot.add_cog(RestartMsg(bot))
