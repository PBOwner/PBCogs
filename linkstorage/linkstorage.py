import discord
from redbot.core import commands, Config
from redbot.core.bot import Red

class LinkStorage(commands.Cog):
    """A cog to store and retrieve links by name."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567891)
        self.config.register_global(links={}, groups={}, allowed_users=[])

    @commands.group()
    async def link(self, ctx: commands.Context):
        """Group command for managing links."""
        pass

    @link.command()
    @commands.is_owner()
    async def add(self, ctx: commands.Context, name: str, link: str, group: str = "default"):
        """Add a link to the storage."""
        async with self.config.groups() as groups:
            if group not in groups:
                await ctx.send(f"Group {group} does not exist. Please create it first.")
                return
            groups[group][name] = link
        await ctx.send(f"Added link: {name} -> {link} to group {group}")

    @link.command()
    @commands.is_owner()
    async def remove(self, ctx: commands.Context, name: str, group: str = "default"):
        """Remove a link from the storage."""
        async with self.config.groups() as groups:
            if group in groups and name in groups[group]:
                del groups[group][name]
                await ctx.send(f"Removed link: {name} from group {group}")
            else:
                await ctx.send(f"No link found with the name: {name} in group {group}")

    @link.command()
    async def get(self, ctx: commands.Context, name: str):
        """Retrieve a link by name."""
        name_lower = name.lower()
        groups = await self.config.groups()
        results = []
        for group, links in groups.items():
            for link_name, link in links.items():
                if link_name.lower() == name_lower:
                    results.append(f"{link_name} -> {link} (Group: {group})")
        if results:
            await ctx.send("\n".join(results))
        else:
            await ctx.send(f"No link found with the name: {name}")

    @link.command()
    async def list(self, ctx: commands.Context):
        """List all stored links."""
        groups = await self.config.groups()
        if groups:
            description = ""
            for group, links in groups.items():
                for name, link in links.items():
                    description += f"{name} -> {link} (Group: {group})\n"
            embed = discord.Embed(description=description, color=discord.Color.blue())
            await ctx.send(embed=embed)
        else:
            await ctx.send("No links stored.")

    @link.command()
    @commands.is_owner()
    async def allow(self, ctx: commands.Context, user: discord.User):
        """Allow a user to add/remove links."""
        async with self.config.allowed_users() as allowed_users:
            if user.id not in allowed_users:
                allowed_users.append(user.id)
                await ctx.send(f"{user} is now allowed to add/remove links.")
            else:
                await ctx.send(f"{user} is already allowed to add/remove links.")

    @link.command()
    @commands.is_owner()
    async def disallow(self, ctx: commands.Context, user: discord.User):
        """Disallow a user from adding/removing links."""
        async with self.config.allowed_users() as allowed_users:
            if user.id in allowed_users:
                allowed_users.remove(user.id)
                await ctx.send(f"{user} is no longer allowed to add/remove links.")
            else:
                await ctx.send(f"{user} is not allowed to add/remove links.")

    @link.command()
    async def useradd(self, ctx: commands.Context, name: str, link: str, group: str = "default"):
        """Add a link to the user's storage."""
        user_id = ctx.author.id
        allowed_users = await self.config.allowed_users()
        if user_id in allowed_users:
            async with self.config.user(user_id).groups() as groups:
                if group not in groups:
                    await ctx.send(f"Group {group} does not exist. Please create it first.")
                    return
                groups[group][name] = link
            await ctx.send(f"Added link: {name} -> {link} to group {group}")
        else:
            await ctx.send("You are not allowed to add links.")

    @link.command()
    async def userremove(self, ctx: commands.Context, name: str, group: str = "default"):
        """Remove a link from the user's storage."""
        user_id = ctx.author.id
        allowed_users = await self.config.allowed_users()
        if user_id in allowed_users:
            async with self.config.user(user_id).groups() as groups:
                if group in groups and name in groups[group]:
                    del groups[group][name]
                    await ctx.send(f"Removed link: {name} from group {group}")
                else:
                    await ctx.send(f"No link found with the name: {name} in group {group}")
        else:
            await ctx.send("You are not allowed to remove links.")

    @link.command()
    async def userlist(self, ctx: commands.Context):
        """List all stored links of the user."""
        user_id = ctx.author.id
        allowed_users = await self.config.allowed_users()
        if user_id in allowed_users:
            groups = await self.config.user(user_id).groups()
            if groups:
                description = ""
                for group, links in groups.items():
                    for name, link in links.items():
                        description += f"{name} -> {link} (Group: {group})\n"
                embed = discord.Embed(description=description, color=discord.Color.blue())
                await ctx.send(embed=embed)
            else:
                await ctx.send("No links stored.")
        else:
            await ctx.send("You are not allowed to list links.")

    @link.command()
    @commands.is_owner()
    async def creategroup(self, ctx: commands.Context, group: str):
        """Create a new group."""
        async with self.config.groups() as groups:
            if group in groups:
                await ctx.send(f"Group {group} already exists.")
            else:
                groups[group] = {}
                await ctx.send(f"Group {group} created.")

    @link.command()
    @commands.is_owner()
    async def deletegroup(self, ctx: commands.Context, group: str):
        """Delete a group."""
        async with self.config.groups() as groups:
            if group in groups:
                del groups[group]
                await ctx.send(f"Group {group} deleted.")
            else:
                await ctx.send(f"Group {group} does not exist.")

    @link.command()
    async def listgroups(self, ctx: commands.Context):
        """List all groups."""
        groups = await self.config.groups()
        if groups:
            group_names = "\n".join(groups.keys())
            await ctx.send(f"Groups:\n{group_names}")
        else:
            await ctx.send("No groups available.")
