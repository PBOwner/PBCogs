import discord
from discord.ext import commands
from redbot.core import commands

class ServerInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def serverinfo(self, ctx, invite_link: str):
        """Fetches server information using an invite link and displays it in an embed."""
        try:
            # Extract the invite code from the link
            invite_code = invite_link.split('/')[-1]
            invite = await self.bot.fetch_invite(invite_code)

            # Extract available information from the invite
            guild = invite.guild
            guild_name = guild.name
            guild_id = guild.id
            member_count = invite.approximate_member_count
            online_count = invite.approximate_presence_count
            icon_hash = guild.icon
            icon_url = f"https://cdn.discordapp.com/icons/{guild_id}/{icon_hash}.png" if icon_hash else None

            # Create an embed with the extracted information
            embed = discord.Embed(title=f"Server Info: {guild_name}", color=discord.Color.blue())
            if icon_url:
                embed.set_thumbnail(url=icon_url)
            embed.add_field(name="Guild ID", value=guild_id, inline=True)
            embed.add_field(name="Member Count", value=member_count, inline=True)
            embed.add_field(name="Online Members", value=online_count, inline=True)

            await ctx.send(embed=embed)
        except discord.NotFound:
            await ctx.send("Invalid invite link or the invite has expired.")
        except discord.HTTPException as e:
            await ctx.send(f"An error occurred while fetching the invite: {str(e)}")

def setup(bot):
    bot.add_cog(ServerInfo(bot))
