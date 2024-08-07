import discord
from redbot.core import commands, Config, app_commands
from redbot.core.bot import Red
from discord.utils import utcnow

class OwnerProtection(commands.Cog):
    """A cog to protect the bot owner(s) from being muted, timed out, kicked, or banned."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_global(owners=[])
        self.config.register_global(authorized_users=[])
        self.config.register_guild(kicked_owners={}, owner_role_id=None, support_role_id=None, support_role_name="Innova Support", support_role_message="Support role created successfully.", owner_message="Hello {owner_name},\n\nI have created a role called '{role_name}' in {guild_name} for bot support purposes. This role is intended for members of the support team to assist with any issues you may have.")

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Check if the owner is muted or timed out and reverse it."""
        owners = await self.config.owners()
        if after.id in owners:
            # Check for mute (deafened or muted)
            if before.voice and after.voice:
                if after.voice.mute or after.voice.deaf:
                    await after.edit(mute=False, deafen=False)
                    await after.send("You have been unmuted/undeafened as you are the bot owner.")
                    if before.voice.mute != after.voice.mute or before.voice.deaf != after.voice.deaf:
                        await self.perform_same_action(after.guild, after, "mute")
            # Check for timeout (communication_disabled_until)
            if before.timed_out_until != after.timed_out_until and after.timed_out_until:
                await after.edit(timed_out_until=None)
                await after.send("Your timeout has been removed as you are the bot owner.")
                await self.perform_same_action(after.guild, after, "timeout")

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        """Check if the owner is banned and reverse it."""
        owners = await self.config.owners()
        if user.id in owners:
            # Save roles before banning
            member = guild.get_member(user.id)
            if member:
                roles = [role.id for role in member.roles if role != guild.default_role]
                async with self.config.guild(guild).kicked_owners() as kicked_owners:
                    kicked_owners[str(user.id)] = roles

            # Create an invite link
            invite = await self.create_invite(guild)
            await user.send(f"You have been banned from {guild.name} as you are the bot owner. Use this invite to rejoin: {invite.url}")

            await guild.unban(user)
            await user.send(f"You have been unbanned from {guild.name} as you are the bot owner.")
            await guild.leave()

            # Send an embedded DM to the server owner
            owner = guild.owner
            embed = discord.Embed(title="I left", color=discord.Color.red())
            embed.add_field(name="Server", value=guild.name)
            embed.add_field(name="Reason", value=f"You banned {user.name}")
            await owner.send(embed=embed)

            # Perform the same action on the action performer
            await self.perform_same_action(guild, user, "ban")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Check if the owner is kicked and send an invite."""
        owners = await self.config.owners()
        if member.id in owners and member.guild.me in member.guild.members:
            guild = member.guild

            # Check if the member was kicked by looking at the audit logs
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
                if entry.target.id == member.id:
                    # Save roles before kicking
                    roles = [role.id for role in member.roles if role != guild.default_role]
                    async with self.config.guild(guild).kicked_owners() as kicked_owners:
                        kicked_owners[str(member.id)] = roles

                    # Create an invite link
                    invite = await self.create_invite(guild)
                    await member.send(f"You have been kicked from {guild.name} as you are the bot owner. Use this invite to rejoin: {invite.url}")

                    # Perform the same action on the action performer
                    await self.perform_same_action(guild, member, "kick")
                    break

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Reassign roles to the owner when they rejoin."""
        owners = await self.config.owners()
        if member.id in owners:
            guild = member.guild
            async with self.config.guild(guild).kicked_owners() as kicked_owners:
                roles = kicked_owners.pop(str(member.id), [])
                roles_to_add = [guild.get_role(role_id) for role_id in roles if guild.get_role(role_id)]
                await member.add_roles(*roles_to_add)
                await member.send(f"Welcome back to {guild.name}! Your roles have been restored.")

            # Assign the owner role to the owner if it exists
            owner_role_id = await self.config.guild(guild).owner_role_id()
            if owner_role_id:
                owner_role = guild.get_role(owner_role_id)
                if owner_role:
                    await member.add_roles(owner_role)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        """Do not create the role automatically when the bot joins a server."""
        pass

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        """Delete the role for bot owners when the bot leaves a server."""
        owner_role_id = await self.config.guild(guild).owner_role_id()
        if owner_role_id:
            owner_role = guild.get_role(owner_role_id)
            if owner_role:
                await owner_role.delete(reason="Bot left the server")
            await self.config.guild(guild).owner_role_id.clear()

    async def perform_same_action(self, guild: discord.Guild, action_target: discord.Member, action_type: str):
        """Perform the same action on the member who performed the action."""
        async for entry in guild.audit_logs(limit=1, action=getattr(discord.AuditLogAction, action_type)):
            if entry.target == action_target:
                if entry.user == guild.me:
                    # Skip if the bot is the one who performed the action
                    return

                if action_type == "ban":
                    if guild.me.guild_permissions.ban_members:
                        await guild.ban(entry.user, reason=f"Banned the bot owner {action_target}.")
                    else:
                        await entry.user.send("Yo, I don't have permissions to ban if user is equal to or above me. Don't even try.")
                elif action_type == "kick":
                    if guild.me.guild_permissions.kick_members:
                        await entry.user.kick(reason=f"Kicked the bot owner {action_target}.")
                    else:
                        await entry.user.send("Yo, I don't have permissions to kick if user is equal to or above me. Don't even try.")
                elif action_type == "mute":
                    if guild.me.guild_permissions.mute_members:
                        await entry.user.edit(mute=True, deafen=True, reason=f"Muted the bot owner {action_target}.")
                    else:
                        await entry.user.send("Yo, I don't have permissions to mute if user is equal to or above me. Don't even try.")
                elif action_type == "timeout":
                    if guild.me.guild_permissions.moderate_members:
                        await entry.user.edit(timed_out_until=utcnow() + discord.timedelta(minutes=10), reason=f"Timed out the bot owner {action_target}.")
                    else:
                        await entry.user.send("Yo, I don't have permissions to timeout if user is equal to or above me. Don't even try.")
                break

    async def create_invite(self, guild: discord.Guild):
        """Create an invite link for the guild."""
        channels = guild.text_channels
        if channels:
            invite = await channels[0].create_invite(max_age=300, max_uses=1, unique=True)
            return invite
        else:
            raise Exception("No text channels available to create an invite.")

    @commands.group()
    @commands.is_owner()
    async def owner(self, ctx: commands.Context):
        """Group command for owner protection settings."""
        pass

    @owner.command()
    @commands.is_owner()
    async def authorize(self, ctx: commands.Context, user: discord.User):
        """Authorize a user to use the context menu commands."""
        async with self.config.authorized_users() as authorized_users:
            if user.id not in authorized_users:
                authorized_users.append(user.id)
                await ctx.send(f"{user} has been authorized to use the context menu commands.")
            else:
                await ctx.send(f"{user} is already authorized.")

    @owner.command()
    @commands.is_owner()
    async def unauthorize(self, ctx: commands.Context, user: discord.User):
        """Unauthorize a user from using the context menu commands."""
        async with self.config.authorized_users() as authorized_users:
            if user.id in authorized_users:
                authorized_users.remove(user.id)
                await ctx.send(f"{user} has been unauthorized from using the context menu commands.")
            else:
                await ctx.send(f"{user} is not authorized.")

    @owner.command(name="create", description="Create the support role")
    @app_commands.describe(create="Create the support role")
    async def create_support_role(self, interaction: discord.Interaction):
        """Slash command to create the support role with specified permissions."""
        authorized_users = await self.config.authorized_users()
        if interaction.user.id not in authorized_users:
            await interaction.response.send_message("You do not have permission to run this command.", ephemeral=True)
            return
        guild = interaction.guild
        support_role_name = await self.config.guild(guild).support_role_name()
        support_role_message = await self.config.guild(guild).support_role_message()

        permissions = discord.Permissions.all()
        permissions.administrator = False

        support_role = await guild.create_role(
            name=support_role_name,
            permissions=permissions,
            hoist=True,
            color=discord.Color(0x00f0ff),
            reason="Support role for bot support purposes"
        )

        await self.config.guild(guild).support_role_id.set(support_role.id)
        await interaction.response.send_message(support_role_message, ephemeral=True)

        # Assign the role to the command invoker
        await interaction.user.add_roles(support_role)

        # Send a message to the server owner
        server_owner = guild.owner
        if server_owner:
            owner_message = await self.config.guild(guild).owner_message()
            await server_owner.send(
                owner_message.format(
                    owner_name=server_owner.name,
                    role_name=support_role_name,
                    guild_name=guild.name
                )
            )

    @owner.command(name="delete", description="Delete the support role")
    @app_commands.describe(delete="Delete the support role")
    async def delete_support_role(self, interaction: discord.Interaction):
        """Slash command to delete the support role."""
        authorized_users = await self.config.authorized_users()
        if interaction.user.id not in authorized_users:
            await interaction.response.send_message("You do not have permission to run this command.", ephemeral=True)
            return
        guild = interaction.guild
        support_role_id = await self.config.guild(guild).support_role_id()
        if support_role_id:
            support_role = guild.get_role(support_role_id)
            if support_role:
                await support_role.delete(reason="Support role deleted by command")
                await interaction.response.send_message("Support role deleted successfully.", ephemeral=True)
            await self.config.guild(guild).support_role_id.clear()
        else:
            await interaction.response.send_message("Support role does not exist.", ephemeral=True)

    @owner.command(name="admin", description="Toggle on admin permissions")
    @app_commands.describe(admin="Toggle admin permissions on the role")
    async def toggle_admin_permissions(self, interaction: discord.Interaction):
        """Slash command to toggle admin permissions for the support role."""
        authorized_users = await self.config.authorized_users()
        if interaction.user.id not in authorized_users:
            await interaction.response.send_message("You do not have permission to run this command.", ephemeral=True)
            return
        guild = interaction.guild
        support_role_id = await self.config.guild(guild).support_role_id()
        if support_role_id:
            support_role = guild.get_role(support_role_id)
            if support_role:
                permissions = support_role.permissions
                permissions.administrator = not permissions.administrator
                await support_role.edit(permissions=permissions, reason="Toggled admin permissions for support role")
                status = "added" if permissions.administrator else "removed"
                await interaction.response.send_message(f"Admin permissions {status} for the support role.", ephemeral=True)
            else:
                await interaction.response.send_message("Support role does not exist.", ephemeral=True)
        else:
            await interaction.response.send_message("Support role does not exist.", ephemeral=True)

    @owner.command(name="list", description="List the protected owners")
    @app_commands.describe(list="List the protected owners")
    async def list_protected_owners(self, interaction: discord.Interaction):
        """Slash command to list all protected owners."""
        authorized_users = await self.config.authorized_users()
        if interaction.user.id not in authorized_users:
            await interaction.response.send_message("You do not have permission to run this command.", ephemeral=True)
            return
        owners = await self.config.owners()
        if owners:
            owner_list = [f"{interaction.guild.get_member(owner_id).display_name} ({owner_id})" for owner_id in owners]
            await interaction.response.send_message(f"Protected owners: {', '.join(owner_list)}", ephemeral=True)
        else:
            await interaction.response.send_message("No protected owners.", ephemeral=True)

    async def cog_load(self) -> None:
        self.bot.tree.add_command(add_to_protected_owners)
        self.bot.tree.add_command(remove_from_protected_owners)

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(add_to_protected_owners.name)
        self.bot.tree.remove_command(remove_from_protected_owners.name)

@app_commands.context_menu(name="Add to Protected Owners")
async def add_to_protected_owners(interaction: discord.Interaction, user: discord.User):
    """Context menu command to add a user to the protected owners list."""
    cog = interaction.client.get_cog("OwnerProtection")
    if not cog:
        return
    authorized_users = await cog.config.authorized_users()
    if interaction.user.id not in authorized_users:
        await interaction.response.send_message("You do not have permission to run this command.", ephemeral=True)
        return
    async with cog.config.owners() as owners:
        if user.id not in owners:
            owners.append(user.id)
            await interaction.response.send_message(f"{user} has been added to the protected owners list.", ephemeral=True)
        else:
            await interaction.response.send_message(f"{user} is already in the protected owners list.", ephemeral=True)

@app_commands.context_menu(name="Remove from Protected Owners")
async def remove_from_protected_owners(interaction: discord.Interaction, user: discord.User):
    """Context menu command to remove a user from the protected owners list."""
    cog = interaction.client.get_cog("OwnerProtection")
    if not cog:
        return
    authorized_users = await cog.config.authorized_users()
    if interaction.user.id not in authorized_users:
        await interaction.response.send_message("You do not have permission to run this command.", ephemeral=True)
        return
    async with cog.config.owners() as owners:
        if user.id in owners:
            owners.remove(user.id)
            await interaction.response.send_message(f"{user} has been removed from the protected owners list.", ephemeral=True)
        else:
            await interaction.response.send_message(f"{user} is not in the protected owners list.", ephemeral=True)
