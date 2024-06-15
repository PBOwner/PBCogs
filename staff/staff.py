import discord
from redbot.core import Config, checks, commands

class StaffManager(commands.Cog):
    """Staff Manager cog for managing staff roles and blacklisting users."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "staff_updates_channel": None
        }
        self.config.register_guild(**default_guild)

    @commands.guild_only()
    @commands.admin_or_permissions(manage_roles=True)
    @commands.command()
    async def setstaffupdates(self, ctx, channel: discord.TextChannel):
        """Set the channel for staff updates."""
        await self.config.guild(ctx.guild).staff_updates_channel.set(channel.id)
        await ctx.send(f"Staff updates channel set to {channel.mention}")

    @commands.guild_only()
    @commands.admin_or_permissions(manage_roles=True)
    @commands.command()
    async def fire(self, ctx, member: discord.Member, role: discord.Role):
        """Fire a staff member by removing a role."""
        await member.remove_roles(role)
        await self.send_update(ctx.guild, f"{member.mention} was fired from the role {role.name}")

    @commands.guild_only()
    @commands.admin_or_permissions(manage_roles=True)
    @commands.command()
    async def hire(self, ctx, member: discord.Member, role: discord.Role):
        """Hire a staff member by adding a role."""
        await member.add_roles(role)
        await self.send_update(ctx.guild, f"{member.mention} was hired for the role {role.name}")

    @commands.guild_only()
    @commands.admin_or_permissions(manage_roles=True)
    @commands.command()
    async def demote(self, ctx, member: discord.Member, role: discord.Role):
        """Demote a staff member by removing a role."""
        await member.remove_roles(role)
        await self.send_update(ctx.guild, f"{member.mention} was demoted from the role {role.name}")

    @commands.guild_only()
    @commands.admin_or_permissions(manage_roles=True)
    @commands.command()
    async def promote(self, ctx, member: discord.Member, role: discord.Role):
        """Promote a staff member by adding a role."""
        await member.add_roles(role)
        await self.send_update(ctx.guild, f"{member.mention} was promoted to the role {role.name}")

    @commands.guild_only()
    @commands.admin_or_permissions(kick_members=True)
    @commands.command()
    async def blacklist(self, ctx, member: discord.Member, reason: str, proof: str):
        """Blacklist a user by kicking them from the server with a reason and proof."""
        await member.kick(reason=reason)
        await self.send_update(ctx.guild, f"{member.id} was blacklisted from {ctx.guild.name} for {reason} with {proof}")

    async def send_update(self, guild, message):
        """Send a staff update message to the configured channel."""
        channel_id = await self.config.guild(guild).staff_updates_channel()
        if channel_id:
            channel = guild.get_channel(channel_id)
            if channel:
                await channel.send(message)
            else:
                print(f"Channel ID {channel_id} not found in guild {guild.name}")
        else:
            print(f"No staff updates channel set for guild {guild.name}")

def setup(bot):
    bot.add_cog(StaffManager(bot))
