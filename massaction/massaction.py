from redbot.core import commands, checks, Config
import discord
from datetime import timedelta

class MassAction(commands.Cog):
    """Cog for mass banning, kicking, muting, and timing out members in a role."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "mute_role": None
        }
        self.config.register_guild(**default_guild)

    @commands.group(name="mass")
    @checks.admin_or_permissions(administrator=True)
    async def mass(self, ctx):
        """Group command for mass actions."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid mass command. Use `mass ban`, `mass kick`, `mass mute`, or `mass timeout`.")

    @mass.command(name="ban")
    @checks.admin_or_permissions(ban_members=True)
    async def mass_ban(self, ctx, role: discord.Role):
        """Ban all members in a specified role."""
        members = role.members
        if not members:
            await ctx.send(f"No members found in the role {role.name}.")
            return

        results = []

        for member in members:
            try:
                await member.ban(reason=f"Banned by {ctx.author} using massban command.")
                results.append(f"Banned {member.name}")
            except discord.Forbidden:
                results.append(f"Failed to ban {member.name}")
            except discord.HTTPException as e:
                results.append(f"An error occurred with {member.name}: {e}")

        embed = discord.Embed(title="Mass Ban Results", description="\n".join(results), color=discord.Color.red())
        await ctx.send(embed=embed)

    @mass.command(name="kick")
    @checks.admin_or_permissions(kick_members=True)
    async def mass_kick(self, ctx, role: discord.Role):
        """Kick all members in a specified role."""
        members = role.members
        if not members:
            await ctx.send(f"No members found in the role {role.name}.")
            return

        results = []

        for member in members:
            try:
                await member.kick(reason=f"Kicked by {ctx.author} using masskick command.")
                results.append(f"Kicked {member.name}")
            except discord.Forbidden:
                results.append(f"Failed to kick {member.name}")
            except discord.HTTPException as e:
                results.append(f"An error occurred with {member.name}: {e}")

        embed = discord.Embed(title="Mass Kick Results", description="\n".join(results), color=discord.Color.orange())
        await ctx.send(embed=embed)

    @mass.command(name="mute")
    @checks.admin_or_permissions(manage_roles=True)
    async def mass_mute(self, ctx, role: discord.Role):
        """Mute all members in a specified role by adding a mute role."""
        mute_role_id = await self.config.guild(ctx.guild).mute_role()
        if mute_role_id is None:
            await ctx.send("Mute role is not set. Use `mass setmute` to set it.")
            return

        mute_role = ctx.guild.get_role(mute_role_id)
        if mute_role is None:
            await ctx.send("Mute role not found. Please set a valid mute role using `mass setmute`.")
            return

        members = role.members
        if not members:
            await ctx.send(f"No members found in the role {role.name}.")
            return

        results = []

        for member in members:
            try:
                await member.add_roles(mute_role, reason=f"Muted by {ctx.author} using massmute command.")
                results.append(f"Muted {member.name}")
            except discord.Forbidden:
                results.append(f"Failed to mute {member.name}")
            except discord.HTTPException as e:
                results.append(f"An error occurred with {member.name}: {e}")

        embed = discord.Embed(title="Mass Mute Results", description="\n".join(results), color=discord.Color.blue())
        await ctx.send(embed=embed)

    @mass.command(name="timeout")
    @checks.admin_or_permissions(moderate_members=True)
    async def mass_timeout(self, ctx, role: discord.Role, duration: int):
        """Timeout all members in a specified role for a given duration in minutes."""
        members = role.members
        if not members:
            await ctx.send(f"No members found in the role {role.name}.")
            return

        timeout_duration = timedelta(minutes=duration)
        results = []

        for member in members:
            try:
                await member.edit(timed_out_until=discord.utils.utcnow() + timeout_duration, reason=f"Timed out by {ctx.author} using masstimeout command.")
                results.append(f"Timed out {member.name} for {duration} minutes")
            except discord.Forbidden:
                results.append(f"Failed to timeout {member.name}")
            except discord.HTTPException as e:
                results.append(f"An error occurred with {member.name}: {e}")

        embed = discord.Embed(title="Mass Timeout Results", description="\n".join(results), color=discord.Color.purple())
        await ctx.send(embed=embed)

    @mass.command(name="setmute")
    @checks.admin_or_permissions(manage_roles=True)
    async def set_mute_role(self, ctx, role: discord.Role):
        """Set the mute role for this server."""
        await self.config.guild(ctx.guild).mute_role.set(role.id)
        await ctx.send(f"Mute role set to {role.name}.")
