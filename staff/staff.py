import discord
from redbot.core import commands, Config, checks
from redbot.core.bot import Red

class StaffManager(commands.Cog):
    """Staff Manager cog for managing staff roles and blacklist functionality"""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "blacklist_channel": None
        }
        self.config.register_guild(**default_guild)

    @commands.command()
    @commands.guild_only()
    @checks.admin_or_permissions(manage_roles=True)
    async def hire(self, ctx, member: discord.Member, role: discord.Role):
        """Hire a member by assigning them a new role"""
        await member.add_roles(role)
        await ctx.send(f"{member.mention} has been hired as {role.name}.")

    @commands.command()
    @commands.guild_only()
    @checks.admin_or_permissions(manage_roles=True)
    async def fire(self, ctx, member: discord.Member, role: discord.Role):
        """Fire a member by removing their role"""
        await member.remove_roles(role)
        await ctx.send(f"{member.mention} has been fired from {role.name}.")

    @commands.command()
    @commands.guild_only()
    @checks.admin_or_permissions(manage_roles=True)
    async def promote(self, ctx, member: discord.Member, new_role: discord.Role):
        """Promote a member by assigning them a new role"""
        await member.add_roles(new_role)
        await ctx.send(f"{member.mention} has been promoted to {new_role.name}.")

    @commands.command()
    @commands.guild_only()
    @checks.admin_or_permissions(manage_roles=True)
    async def demote(self, ctx, member: discord.Member, new_role: discord.Role):
        """Demote a member by assigning them a new role"""
        await member.add_roles(new_role)
        await ctx.send(f"{member.mention} has been demoted to {new_role.name}.")

    @commands.command()
    @commands.guild_only()
    @checks.admin_or_permissions(kick_members=True)
    async def staffblacklist(self, ctx, member: discord.Member, reason: str, proof: str):
        """Blacklist a member by kicking them from the server with a reason and proof"""
        blacklist_channel_id = await self.config.guild(ctx.guild).blacklist_channel()
        blacklist_channel = ctx.guild.get_channel(blacklist_channel_id)

        if not blacklist_channel:
            await ctx.send("Blacklist channel is not set. Please configure it using the `setblacklistchannel` command.")
            return

        await member.kick(reason=reason)
        await blacklist_channel.send(f"{member.id} was blacklisted from {ctx.guild.name} for {reason} with {proof}.")
        await ctx.send(f"{member.mention} has been blacklisted for {reason} with proof {proof}.")

    @commands.command()
    @commands.guild_only()
    @checks.admin_or_permissions(administrator=True)
    async def setblacklistchannel(self, ctx, channel: discord.TextChannel):
        """Set the channel where blacklist notifications will be sent"""
        await self.config.guild(ctx.guild).blacklist_channel.set(channel.id)
        await ctx.send(f"Blacklist notifications will be sent to {channel.mention}.")

def setup(bot: Red):
    bot.add_cog(StaffManager(bot))
