import discord
from discord.ext import commands

class ServerInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def serverinfo(self, ctx, invite_link: str):
        """Fetches server information from an invite link and displays it in an embed."""
        try:
            # Extract the invite code from the link
            invite_code = invite_link.split('/')[-1]
            invite = await self.bot.fetch_invite(invite_code)

            guild = invite.guild
            owner = guild.owner
            banner_url = guild.banner_url if guild.banner_url else "No Banner"
            description = guild.description if guild.description else "No Description"
            member_count = guild.approximate_member_count
            online_count = guild.approximate_presence_count

            embed = discord.Embed(title=f"Server Info: {guild.name}", color=discord.Color.blue())
            embed.set_thumbnail(url=guild.icon_url)
            embed.add_field(name="Owner Name", value=owner.name, inline=False)
            embed.add_field(name="Owner ID", value=owner.id, inline=False)
            embed.add_field(name="Owner Username", value=str(owner), inline=False)
            embed.add_field(name="Description", value=description, inline=False)
            embed.add_field(name="Member Count", value=member_count, inline=True)
            embed.add_field(name="Online Members", value=online_count, inline=True)
            embed.add_field(name="Invite Code", value=invite_code, inline=True)
            embed.set_image(url=banner_url)

            await ctx.send(embed=embed)
        except discord.NotFound:
            await ctx.send("Invalid invite link or the invite has expired.")
        except discord.HTTPException as e:
            await ctx.send(f"An error occurred while fetching the invite: {str(e)}")

def setup(bot):
    bot.add_cog(ServerInfo(bot))
