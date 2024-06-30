import discord
from redbot.core import commands
from discord.ext import commands as dpy_commands

class RoleMembers(commands.Cog):
    """A cog to list all members in a specified role."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def rolemembers(self, ctx, *, role: str):
        """Shows all members in the specified role by mention or ID."""
        guild = ctx.guild
        role_obj = None

        # Check if the input is a mention or a role ID
        if role.isdigit():
            role_obj = discord.utils.get(guild.roles, id=int(role))
        else:
            role_obj = discord.utils.get(guild.roles, name=role)

        if role_obj is None:
            await ctx.send("Role not found. Please mention the role or provide a valid role ID.")
            return

        members = [member.mention for member in role_obj.members]
        if members:
            embed = discord.Embed(title=f"Members in {role_obj.name}", description="\n".join(members), color=role_obj.color)
        else:
            embed = discord.Embed(title=f"Members in {role_obj.name}", description="No members found in this role.", color=role_obj.color)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(RoleMembers(bot))
