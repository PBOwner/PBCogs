import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
from datetime import datetime, timezone

class RoleManager(commands.Cog):
    """A cog to manage roles based on member statuses and activities."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_guild(
            status_roles={},
            activity_roles={},
            log_channel=None,
            role_list_channel=None,
            embed_message_id=None
        )

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        """Handle presence updates to apply roles based on status and activities."""
        guild = after.guild
        log_channel_id = await self.config.guild(guild).log_channel()
        log_channel = guild.get_channel(log_channel_id) if log_channel_id else None

        # Handle status roles
        status_roles = await self.config.guild(guild).status_roles()
        if before.status != after.status:
            role_id = status_roles.get(str(after.status))
            if role_id:
                role = guild.get_role(role_id)
                if role:
                    await after.add_roles(role, reason="Status role assignment")
                    if log_channel:
                        embed = discord.Embed(
                            title="Status Role Assigned",
                            description=f"{after.mention} has been given the role {role.mention} for being {after.status}.",
                            color=discord.Color.green(),
                            timestamp=datetime.now(timezone.utc)
                        )
                        await log_channel.send(embed=embed)
                    await self.update_role_list_embed(guild)

        # Handle activity roles
        activity_roles = await self.config.guild(guild).activity_roles()
        for activity in after.activities:
            role_id = activity_roles.get(activity.name)
            if role_id:
                role = guild.get_role(role_id)
                if role:
                    await after.add_roles(role, reason="Activity role assignment")
                    if log_channel:
                        embed = discord.Embed(
                            title="Activity Role Assigned",
                            description=f"{after.mention} has been given the role {role.mention} for activity {activity.name}.",
                            color=discord.Color.blue(),
                            timestamp=datetime.now(timezone.utc)
                        )
                        await log_channel.send(embed=embed)
                    await self.update_role_list_embed(guild)

    async def update_role_list_embed(self, guild: discord.Guild):
        """Update the role assignment embed in the role list channel."""
        role_list_channel_id = await self.config.guild(guild).role_list_channel()
        embed_message_id = await self.config.guild(guild).embed_message_id()
        role_list_channel = guild.get_channel(role_list_channel_id) if role_list_channel_id else None

        if not role_list_channel:
            return

        status_roles = await self.config.guild(guild).status_roles()
        activity_roles = await self.config.guild(guild).activity_roles()

        embed = discord.Embed(
            title="Role Assignments",
            color=discord.Color.blue()
        )

        if status_roles:
            status_roles_desc = "\n".join([f"{status}: <@&{role_id}>" for status, role_id in status_roles.items()])
        else:
            status_roles_desc = "No status roles set."

        if activity_roles:
            activity_roles_desc = "\n".join([f"{activity}: <@&{role_id}>" for activity, role_id in activity_roles.items()])
        else:
            activity_roles_desc = "No activity roles set."

        embed.add_field(name="Status Roles", value=status_roles_desc, inline=False)
        embed.add_field(name="Activity Roles", value=activity_roles_desc, inline=False)

        if embed_message_id:
            try:
                message = await role_list_channel.fetch_message(embed_message_id)
                await message.edit(embed=embed)
            except discord.NotFound:
                message = await role_list_channel.send(embed=embed)
                await self.config.guild(guild).embed_message_id.set(message.id)
        else:
            message = await role_list_channel.send(embed=embed)
            await self.config.guild(guild).embed_message_id.set(message.id)

    @commands.group()
    @commands.guild_only()
    @commands.admin()
    async def rolemanager(self, ctx: commands.Context):
        """Group command for managing role assignments based on status and activities."""
        pass

    @rolemanager.command()
    async def setstatusrole(self, ctx: commands.Context, status: str, role: discord.Role):
        """Set a role to be assigned for a specific member status."""
        async with self.config.guild(ctx.guild).status_roles() as status_roles:
            status_roles[status] = role.id
        embed = discord.Embed(
            title="Status Role Set",
            description=f"Role {role.mention} will be assigned to members with status {status}.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        await self.update_role_list_embed(ctx.guild)

    @rolemanager.command()
    async def setactivityrole(self, ctx: commands.Context, activity: str, role: discord.Role):
        """Set a role to be assigned for a specific member activity."""
        async with self.config.guild(ctx.guild).activity_roles() as activity_roles:
            activity_roles[activity] = role.id
        embed = discord.Embed(
            title="Activity Role Set",
            description=f"Role {role.mention} will be assigned to members with activity {activity}.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
        await self.update_role_list_embed(ctx.guild)

    @rolemanager.command()
    async def setlogchannel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the channel for logging role assignments."""
        await self.config.guild(ctx.guild).log_channel.set(channel.id)
        embed = discord.Embed(
            title="Log Channel Set",
            description=f"Role assignments will be logged in {channel.mention}.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @rolemanager.command()
    async def setrolelistchannel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the channel for the dynamic role list."""
        await self.config.guild(ctx.guild).role_list_channel.set(channel.id)
        embed = discord.Embed(
            title="Role List Channel Set",
            description=f"The dynamic role list will be displayed in {channel.mention}.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        await self.update_role_list_embed(ctx.guild)

    @rolemanager.command()
    async def clearstatusrole(self, ctx: commands.Context, status: str):
        """Clear the role assigned for a specific member status."""
        async with self.config.guild(ctx.guild).status_roles() as status_roles:
            if status in status_roles:
                del status_roles[status]
        embed = discord.Embed(
            title="Status Role Cleared",
            description=f"Role assignment for status {status} has been cleared.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)
        await self.update_role_list_embed(ctx.guild)

    @rolemanager.command()
    async def clearactivityrole(self, ctx: commands.Context, activity: str):
        """Clear the role assigned for a specific member activity."""
        async with self.config.guild(ctx.guild).activity_roles() as activity_roles:
            if activity in activity_roles:
                del activity_roles[activity]
        embed = discord.Embed(
            title="Activity Role Cleared",
            description=f"Role assignment for activity {activity} has been cleared.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)
        await self.update_role_list_embed(ctx.guild)

    @rolemanager.command()
    async def status(self, ctx: commands.Context):
        """Check the current settings for role assignments."""
        guild = ctx.guild
        status_roles = await self.config.guild(guild).status_roles()
        activity_roles = await self.config.guild(guild).activity_roles()
        log_channel_id = await self.config.guild(guild).log_channel()
        role_list_channel_id = await self.config.guild(guild).role_list_channel()
        log_channel = guild.get_channel(log_channel_id) if log_channel_id else "Not set"
        role_list_channel = guild.get_channel(role_list_channel_id) if role_list_channel_id else "Not set"

        embed = discord.Embed(
            title="Role Assignment Settings",
            color=discord.Color.blue()
        )
        embed.add_field(name="Log Channel", value=log_channel, inline=False)
        embed.add_field(name="Role List Channel", value=role_list_channel, inline=False)

        if status_roles:
            status_roles_desc = "\n".join([f"{status}: <@&{role_id}>" for status, role_id in status_roles.items()])
        else:
            status_roles_desc = "No status roles set."

        if activity_roles:
            activity_roles_desc = "\n".join([f"{activity}: <@&{role_id}>" for activity, role_id in activity_roles.items()])
        else:
            activity_roles_desc = "No activity roles set."

        embed.add_field(name="Status Roles", value=status_roles_desc, inline=False)
        embed.add_field(name="Activity Roles", value=activity_roles_desc, inline=False)

        await ctx.send(embed=embed)

def setup(bot: Red):
    bot.add_cog(RoleManager(bot))
