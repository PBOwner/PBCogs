import discord
from redbot.core import Config, checks, commands

class StaffManager(commands.Cog):
    """Staff Manager Cog for managing staff-related actions."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "staff_updates_channel": None,
            "blacklist_channel": None
        }
        self.config.register_guild(**default_guild)

    async def send_embed(self, ctx, title, username, user_id, position, old_position=None):
        """Helper function to send an embed message to the staff updates channel."""
        channel_id = await self.config.guild(ctx.guild).staff_updates_channel()
        if channel_id is None:
            await ctx.send("Staff updates channel is not set. Use `setstaffupdates` to set it.")
            return
        
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            await ctx.send("Staff updates channel not found.")
            return

        embed = discord.Embed(title=title, color=discord.Color.blue())
        embed.add_field(name="Username", value=username, inline=False)
        embed.add_field(name="User ID", value=user_id, inline=False)
        embed.add_field(name="Position", value=position, inline=False)
        if old_position:
            embed.add_field(name="Old Position", value=old_position, inline=False)
        embed.add_field(name="Issuer", value=ctx.author.name, inline=False)
        
        await channel.send(embed=embed)

    @commands.command()
    @checks.admin_or_permissions(manage_roles=True)
    async def fire(self, ctx, member: discord.Member, position: str):
        """Fire a staff member."""
        await self.send_embed(ctx, "Staff Fired", member.name, member.id, position)
        await ctx.send(f"{member.name} has been fired from the position of {position}.")

    @commands.command()
    @checks.admin_or_permissions(manage_roles=True)
    async def hire(self, ctx, member: discord.Member, position: str):
        """Hire a new staff member."""
        await self.send_embed(ctx, "Staff Hired", member.name, member.id, position)
        await ctx.send(f"{member.name} has been hired for the position of {position}.")

    @commands.command()
    @checks.admin_or_permissions(manage_roles=True)
    async def demote(self, ctx, member: discord.Member, old_position: str, new_position: str):
        """Demote a staff member."""
        await self.send_embed(ctx, "Staff Demoted", member.name, member.id, new_position, old_position)
        await ctx.send(f"{member.name} has been demoted from {old_position} to {new_position}.")

    @commands.command()
    @checks.admin_or_permissions(manage_roles=True)
    async def promote(self, ctx, member: discord.Member, old_position: str, new_position: str):
        """Promote a staff member."""
        await self.send_embed(ctx, "Staff Promoted", member.name, member.id, new_position, old_position)
        await ctx.send(f"{member.name} has been promoted from {old_position} to {new_position}.")

    @commands.command()
    async def staffblacklist(self, ctx, member: discord.Member, reason: str, proof: str):
        """Blacklist a staff member."""
        channel_id = await self.config.guild(ctx.guild).blacklist_channel()
        if channel_id is None:
            await ctx.send("Blacklist channel is not set. Use `setblacklistchannel` to set it.")
            return

        channel = self.bot.get_channel(channel_id)
        if channel is None:
            await ctx.send("Blacklist channel not found.")
            return
        await member.kick(reason=reason)
        embed = discord.Embed(title="Staff Blacklisted", color=discord.Color.dark_red())
        embed.add_field(name="Username", value=member.name, inline=False)
        embed.add_field(name="User ID", value=member.id, inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Proof", value=proof, inline=False)
        embed.add_field(name="Issuer", value=ctx.author.name, inline=False)
        await self.blacklist_channel.send(embed=embed)
        await ctx.send(f"{member.id} was blacklisted from {ctx.guild.name} for {reason} with {proof}")

    @commands.command()
    @checks.admin_or_permissions(manage_channels=True)
    async def setstaffupdates(self, ctx, channel: discord.TextChannel):
        """Set the channel for staff updates."""
        await self.config.guild(ctx.guild).staff_updates_channel.set(channel.id)
        await ctx.send(f"Staff updates channel set to {channel.mention}")

    @commands.command()
    @checks.admin_or_permissions(manage_channels=True)
    async def setblacklistchannel(self, ctx, channel: discord.TextChannel):
        """Set the channel for blacklist updates."""
        await self.config.guild(ctx.guild).blacklist_channel.set(channel.id)
        await ctx.send(f"Blacklist channel set to {channel.mention}")

def setup(bot):
    bot.add_cog(StaffManager(bot))
