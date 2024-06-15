import discord
from redbot.core import Config, checks, commands

class StaffManager(commands.Cog):
    """Cog for managing staff members in a Discord server."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "staff_updates_channel": None
        }
        self.config.register_guild(**default_guild)

    async def send_embed(self, ctx, user, new_role, old_role=None, reason=None, proof=None):
        """Helper function to send an embed to the configured channel."""
        channel_id = await self.config.guild(ctx.guild).staff_updates_channel()
        if not channel_id:
            await ctx.send("Staff updates channel is not set. Use `setstaffupdates` to set it.")
            return

        channel = self.bot.get_channel(channel_id)
        if not channel:
            await ctx.send("Configured staff updates channel not found.")
            return

        embed = discord.Embed(title="Staff Update", color=discord.Color.blue())
        embed.add_field(name="Username", value=user.name, inline=False)
        embed.add_field(name="User ID", value=user.id, inline=False)
        embed.add_field(name="Position", value=new_role, inline=False)
        if old_role:
            embed.add_field(name="Old Position", value=old_role, inline=False)
        embed.add_field(name="Issuer", value=ctx.author.name, inline=False)
        if reason:
            embed.add_field(name="Reason", value=reason, inline=False)
        if proof:
            embed.add_field(name="Proof", value=proof, inline=False)

        await channel.send(embed=embed)

    @commands.command()
    @checks.admin_or_permissions(manage_roles=True)
    async def setstaffupdates(self, ctx, channel: discord.TextChannel):
        """Set the channel for staff updates."""
        await self.config.guild(ctx.guild).staff_updates_channel.set(channel.id)
        await ctx.send(f"Staff updates channel set to {channel.mention}")

    @commands.command()
    @checks.admin_or_permissions(manage_roles=True)
    async def hire(self, ctx, user: discord.Member, new_role: discord.Role):
        """Hire a new staff member."""
        await user.add_roles(new_role)
        await self.send_embed(ctx, user, new_role.name)
        await ctx.send(f"{user.mention} has been hired as {new_role.name}")

    @commands.command()
    @checks.admin_or_permissions(manage_roles=True)
    async def fire(self, ctx, user: discord.Member, new_role: discord.Role):
        """Fire a staff member."""
        await user.remove_roles(new_role)
        await self.send_embed(ctx, user, new_role.name)
        await ctx.send(f"{user.mention} has been fired from {new_role.name}")

    @commands.command()
    @checks.admin_or_permissions(manage_roles=True)
    async def promote(self, ctx, user: discord.Member, new_role: discord.Role, old_role: discord.Role):
        """Promote a staff member."""
        await user.add_roles(new_role)
        await user.remove_roles(old_role)
        await self.send_embed(ctx, user, new_role.name, old_role.name)
        await ctx.send(f"{user.mention} has been promoted to {new_role.name}")

    @commands.command()
    @checks.admin_or_permissions(manage_roles=True)
    async def demote(self, ctx, user: discord.Member, new_role: discord.Role, old_role: discord.Role):
        """Demote a staff member."""
        await user.add_roles(new_role)
        await user.remove_roles(old_role)
        await self.send_embed(ctx, user, new_role.name, old_role.name)
        await ctx.send(f"{user.mention} has been demoted to {new_role.name}")

    @commands.command()
    @checks.admin_or_permissions(kick_members=True)
    async def staffblacklist(self, ctx, user: discord.Member, reason: str, proof: str):
        """Blacklist a staff member."""
        await user.kick(reason=reason)
        await self.send_embed(ctx, user, "Blacklisted", reason=reason, proof=proof)
        await ctx.send(f"{user.mention} has been blacklisted for {reason}")

def setup(bot):
    bot.add_cog(StaffManager(bot))
