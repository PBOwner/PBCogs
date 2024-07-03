import discord
import aiohttp
import asyncio
from redbot.core import commands, Config, checks
from redbot.core.bot import Red

class Bl(commands.Cog):
    """A cog to manage a blacklist of users with links in hypertext."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567891)
        self.config.register_guild(blacklist={})
        self.config.register_global(trusted_roles=[])
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        asyncio.create_task(self.session.close())

    @commands.group()
    @commands.guild_only()
    async def bl(self, ctx):
        """Commands to manage the blacklist."""
        pass

    @bl.command()
    @commands.has_permissions(manage_guild=True)
    async def addtrustedrole(self, ctx, role: discord.Role):
        """Add a role to the trusted roles list."""
        async with self.config.trusted_roles() as trusted_roles:
            if role.id not in trusted_roles:
                trusted_roles.append(role.id)
                await ctx.send(f"Role {role.name} added to trusted roles.")
            else:
                await ctx.send(f"Role {role.name} is already a trusted role.")

    @bl.command()
    @commands.has_permissions(manage_guild=True)
    async def removetrustedrole(self, ctx, role: discord.Role):
        """Remove a role from the trusted roles list."""
        async with self.config.trusted_roles() as trusted_roles:
            if role.id in trusted_roles:
                trusted_roles.remove(role.id)
                await ctx.send(f"Role {role.name} removed from trusted roles.")
            else:
                await ctx.send(f"Role {role.name} is not a trusted role.")

    @bl.command()
    async def add(self, ctx, user: discord.User, link: str):
        """Add a user to the blacklist with a link."""
        trusted_roles = await self.config.trusted_roles()
        if not any(role.id in trusted_roles for role in ctx.author.roles):
            await ctx.send("You do not have permission to add to the blacklist.")
            return

        async with self.config.guild(ctx.guild).blacklist() as blacklist:
            blacklist[str(user.id)] = link
            await ctx.send(f"User {user} has been added to the blacklist with link: {link}")

    @bl.command()
    async def remove(self, ctx, user: discord.User):
        """Remove a user from the blacklist."""
        trusted_roles = await self.config.trusted_roles()
        if not any(role.id in trusted_roles for role in ctx.author.roles):
            await ctx.send("You do not have permission to remove from the blacklist.")
            return

        async with self.config.guild(ctx.guild).blacklist() as blacklist:
            if str(user.id) in blacklist:
                del blacklist[str(user.id)]
                await ctx.send(f"User {user} has been removed from the blacklist.")
            else:
                await ctx.send(f"User {user} is not in the blacklist.")

    @bl.command()
    async def check(self, ctx, user: discord.User):
        """Check if a user is in the blacklist."""
        blacklist = await self.config.guild(ctx.guild).blacklist()
        if str(user.id) in blacklist:
            await ctx.send(f"User {user} is blacklisted. Link: {blacklist[str(user.id)]}")
        else:
            await ctx.send(f"User {user} is not in the blacklist.")

    @bl.command()
    async def list(self, ctx):
        """List all blacklisted users."""
        blacklist = await self.config.guild(ctx.guild).blacklist()
        if not blacklist:
            await ctx.send("The blacklist is empty.")
            return

        embed = discord.Embed(title="Blacklisted Users", color=discord.Color.red())
        for user_id, link in blacklist.items():
            user = self.bot.get_user(int(user_id))
            if user:
                embed.add_field(name=str(user), value=f"[Link]({link})", inline=False)
            else:
                embed.add_field(name=f"User ID: {user_id}", value=f"[Link]({link})", inline=False)

        await ctx.send(embed=embed)
