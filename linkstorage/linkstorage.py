import discord
from redbot.core import commands, Config
from redbot.core.bot import Red

class LinkStorage(commands.Cog):
    """A cog to store and retrieve links by name."""

    def __init__(self, bot: Red):
        self.bot = bot
        # Initialize the config with a unique identifier
        self.config = Config.get_conf(self, identifier=1234567891)
        # Register the global configuration structure
        self.config.register_global(links={}, groups={}, allowed_users=[])
        # Register user-specific configuration
        self.config.register_user(groups={})

    @commands.group()
    async def link(self, ctx: commands.Context):
        """Group command for managing links."""
        pass

    @link.command()
    async def add(self, ctx: commands.Context, *, name_link: str):
        """Add a link to the storage."""
        parts = name_link.split()
        link = parts[-1] if parts[-1].startswith("https://") else None
        name = " ".join(parts[:-1]) if link else name_link
        group = "default"

        if link:
            async with self.config.user(ctx.author).groups() as groups:
                if group not in groups:
                    groups[group] = {}
                groups[group][name] = link
            embed = discord.Embed(description=f"Added link: {name} -> {link} to group {group}", color=discord.Color.green())
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(description=f"Invalid link format. The link must start with https://", color=discord.Color.red())
            await ctx.send(embed=embed)

    @link.command()
    async def remove(self, ctx: commands.Context, *, name_group: str):
        """Remove a link from the storage."""
        parts = name_group.split()
        group = parts[-1] if parts[-1].startswith("https://") else "default"
        name = " ".join(parts[:-1]) if group != "default" else name_group

        async with self.config.user(ctx.author).groups() as groups:
            if group in groups and name in groups[group]:
                del groups[group][name]
                embed = discord.Embed(description=f"Removed link: {name} from group {group}", color=discord.Color.green())
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(description=f"No link found with the name: {name} in group {group}", color=discord.Color.red())
                await ctx.send(embed=embed)

    @link.command()
    @commands.is_owner()
    async def adminremove(self, ctx: commands.Context, name: str, group: str = "default"):
        """Remove a link or group by its name (admin only)."""
        async with self.config.all_users() as all_users:
            for user_id, user_data in all_users.items():
                if group in user_data['groups'] and name in user_data['groups'][group]:
                    del user_data['groups'][group][name]
                    embed = discord.Embed(description=f"Admin removed link: {name} from group {group}", color=discord.Color.green())
                    await ctx.send(embed=embed)
                    return
            embed = discord.Embed(description=f"No link found with the name: {name} in group {group}", color=discord.Color.red())
            await ctx.send(embed=embed)

    @link.command()
    async def get(self, ctx: commands.Context, *, name: str):
        """Retrieve a link by name."""
        name_lower = name.lower()
        results = []
        async with self.config.all_users() as all_users:
            for user_id, user_data in all_users.items():
                for group, links in user_data['groups'].items():
                    for link_name, link in links.items():
                        if link_name.lower() == name_lower:
                            results.append(f"{link_name} -> {link} (Group: {group})")
        if results:
            embed = discord.Embed(description="\n".join(results), color=discord.Color.blue())
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(description=f"No link found with the name: {name}", color=discord.Color.red())
            await ctx.send(embed=embed)

    @link.command()
    async def list(self, ctx: commands.Context):
        """List all stored links for the user."""
        groups = await self.config.user(ctx.author).groups()
        if groups:
            sorted_groups = sorted(groups.items())
            pages = []
            description = ""
            for group, links in sorted_groups:
                for name, link in links.items():
                    entry = f"{name} -> {link} (Group: {group})\n"
                    if len(description) + len(entry) > 6000 or len(description.split('\n')) > 25:
                        pages.append(description)
                        description = ""
                    description += entry
            if description:
                pages.append(description)

            embeds = [discord.Embed(description=page, color=discord.Color.blue()) for page in pages]
            await self.paginate(ctx, embeds)
        else:
            embed = discord.Embed(description="No links stored.", color=discord.Color.red())
            await ctx.send(embed=embed)

    @link.command()
    @commands.is_owner()
    async def allow(self, ctx: commands.Context, user: discord.User):
        """Allow a user to override and delete any links and groups."""
        async with self.config.allowed_users() as allowed_users:
            if user.id not in allowed_users:
                allowed_users.append(user.id)
                embed = discord.Embed(description=f"{user} is now allowed to override and delete any links and groups.", color=discord.Color.green())
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(description=f"{user} is already allowed to override and delete any links and groups.", color=discord.Color.red())
                await ctx.send(embed=embed)

    @link.command()
    @commands.is_owner()
    async def disallow(self, ctx: commands.Context, user: discord.User):
        """Disallow a user from overriding and deleting any links and groups."""
        async with self.config.allowed_users() as allowed_users:
            if user.id in allowed_users:
                allowed_users.remove(user.id)
                embed = discord.Embed(description=f"{user} is no longer allowed to override and delete any links and groups.", color=discord.Color.green())
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(description=f"{user} is not allowed to override and delete any links and groups.", color=discord.Color.red())
                await ctx.send(embed=embed)

    @link.command()
    async def useradd(self, ctx: commands.Context, *, name_link: str):
        """Add a link to the user's storage."""
        user_id = ctx.author.id
        parts = name_link.split()
        link = parts[-1] if parts[-1].startswith("https://") else None
        name = " ".join(parts[:-1]) if link else name_link
        group = "default"

        if link:
            async with self.config.user(user_id).groups() as groups:
                if group not in groups:
                    groups[group] = {}
                groups[group][name] = link
            embed = discord.Embed(description=f"Added link: {name} -> {link} to group {group}", color=discord.Color.green())
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(description=f"Invalid link format. The link must start with https://", color=discord.Color.red())
            await ctx.send(embed=embed)

    @link.command()
    async def userremove(self, ctx: commands.Context, *, name_group: str):
        """Remove a link from the user's storage."""
        user_id = ctx.author.id
        parts = name_group.split()
        group = parts[-1] if parts[-1].startswith("https://") else "default"
        name = " ".join(parts[:-1]) if group != "default" else name_group

        async with self.config.user(user_id).groups() as groups:
            if group in groups and name in groups[group]:
                del groups[group][name]
                embed = discord.Embed(description=f"Removed link: {name} from group {group}", color=discord.Color.green())
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(description=f"No link found with the name: {name} in group {group}", color=discord.Color.red())
                await ctx.send(embed=embed)

    @link.command()
    async def userlist(self, ctx: commands.Context):
        """List all stored links of the user."""
        user_id = ctx.author.id
        groups = await self.config.user(user_id).groups()
        if groups:
            sorted_groups = sorted(groups.items())
            pages = []
            description = ""
            for group, links in sorted_groups:
                for name, link in links.items():
                    entry = f"{name} -> {link} (Group: {group})\n"
                    if len(description) + len(entry) > 6000 or len(description.split('\n')) > 25:
                        pages.append(description)
                        description = ""
                    description += entry
            if description:
                pages.append(description)

            embeds = [discord.Embed(description=page, color=discord.Color.blue()) for page in pages]
            await self.paginate(ctx, embeds)
        else:
            embed = discord.Embed(description="No links stored.", color=discord.Color.red())
            await ctx.send(embed=embed)

    @link.command()
    async def creategroup(self, ctx: commands.Context, group: str):
        """Create a new group."""
        user_id = ctx.author.id
        async with self.config.user(user_id).groups() as groups:
            if group in groups:
                embed = discord.Embed(description=f"Group {group} already exists.", color=discord.Color.red())
                await ctx.send(embed=embed)
            else:
                groups[group] = {}
                embed = discord.Embed(description=f"Group {group} created.", color=discord.Color.green())
                await ctx.send(embed=embed)

    @link.command()
    async def deletegroup(self, ctx: commands.Context, group: str):
        """Delete a group."""
        user_id = ctx.author.id
        async with self.config.user(user_id).groups() as groups:
            if group in groups:
                del groups[group]
                embed = discord.Embed(description=f"Group {group} deleted.", color=discord.Color.green())
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(description=f"Group {group} does not exist.", color=discord.Color.red())
                await ctx.send(embed=embed)

    @link.command()
    async def listgroups(self, ctx: commands.Context):
        """List all groups."""
        user_id = ctx.author.id
        groups = await self.config.user(user_id).groups()
        if groups:
            group_names = "\n".join(groups.keys())
            embed = discord.Embed(description=f"Groups:\n{group_names}", color=discord.Color.blue())
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(description="No groups available.", color=discord.Color.red())
            await ctx.send(embed=embed)

    async def paginate(self, ctx, embeds):
        """Helper function to paginate embeds."""
        current_page = 0
        message = await ctx.send(embed=embeds[current_page])

        await message.add_reaction("◀️")
        await message.add_reaction("▶️")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["◀️", "▶️"] and reaction.message.id == message.id

        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
                if str(reaction.emoji) == "▶️" and current_page < len(embeds) - 1:
                    current_page += 1
                    await message.edit(embed=embeds[current_page])
                elif str(reaction.emoji) == "◀️" and current_page > 0:
                    current_page -= 1
                    await message.edit(embed=embeds[current_page])
                await message.remove_reaction(reaction, user)
            except asyncio.TimeoutError:
                break
