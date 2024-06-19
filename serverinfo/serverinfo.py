import requests
from bs4 import BeautifulSoup
from redbot.core import commands

class ServerInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def serverinfo(self, ctx, guild_id: str):
        """Fetches server information from discordlookup.com and displays it in an embed."""
        try:
            # Fetch the webpage content
            url = f'https://discordlookup.com/guild/{guild_id}'
            response = requests.get(url)
            if response.status_code != 200:
                await ctx.send("Failed to fetch data from discordlookup.com.")
                return

            # Parse the webpage content
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract the necessary information
            guild_name = soup.find('h1', {'class': 'title'}).text.strip()
            guild_owner = soup.find('span', {'class': 'owner'}).text.strip()
            member_count = soup.find('span', {'class': 'members'}).text.strip()
            online_count = soup.find('span', {'class': 'online'}).text.strip()
            description = soup.find('div', {'class': 'description'}).text.strip() if soup.find('div', {'class': 'description'}) else "No Description"
            icon_url = soup.find('img', {'class': 'guild-icon'})['src'] if soup.find('img', {'class': 'guild-icon'}) else None

            # Create an embed with the extracted information
            embed = discord.Embed(title=f"Server Info: {guild_name}", color=discord.Color.blue())
            if icon_url:
                embed.set_thumbnail(url=icon_url)
            embed.add_field(name="Owner", value=guild_owner, inline=False)
            embed.add_field(name="Description", value=description, inline=False)
            embed.add_field(name="Member Count", value=member_count, inline=True)
            embed.add_field(name="Online Members", value=online_count, inline=True)
            embed.add_field(name="Guild ID", value=guild_id, inline=True)

            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"An error occurred while fetching the server information: {str(e)}")

def setup(bot):
    bot.add_cog(ServerInfo(bot))
