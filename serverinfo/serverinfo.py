import requests
import discord
from discord.ext import commands
from redbot.core import commands

class ServerInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def serverinfo(self, ctx, guild_id: str):
        """Fetches server information using the Discord API and displays it in an embed."""
        try:
            # Replace with your bot token
            BOT_TOKEN = 'YOUR_BOT_TOKEN_HERE'

            # Define the endpoint URL
            url = f'https://discord.com/api/v10/guilds/{guild_id}'

            # Set up the headers with the bot token
            headers = {
                'Authorization': f'Bot {BOT_TOKEN}',
                'Content-Type': 'application/json'
            }

            # Make the request to the Discord API
            response = requests.get(url, headers=headers)

            # Check if the request was successful
            if response.status_code != 200:
                await ctx.send(f"Failed to fetch data from Discord API: {response.status_code}")
                return

            guild_info = response.json()

            # Extract the necessary information
            guild_name = guild_info.get('name', 'Unknown')
            guild_owner_id = guild_info.get('owner_id', 'Unknown')
            member_count = guild_info.get('approximate_member_count', 'Unknown')
            description = guild_info.get('description', 'No Description')
            icon_hash = guild_info.get('icon', None)
            icon_url = f"https://cdn.discordapp.com/icons/{guild_id}/{icon_hash}.png" if icon_hash else None

            # Fetch owner username
            owner_url = f'https://discord.com/api/v10/users/{guild_owner_id}'
            owner_response = requests.get(owner_url, headers=headers)
            owner_info = owner_response.json()
            guild_owner = owner_info.get('username', 'Unknown')

            # Create an embed with the extracted information
            embed = discord.Embed(title=f"Server Info: {guild_name}", color=discord.Color.blue())
            if icon_url:
                embed.set_thumbnail(url=icon_url)
            embed.add_field(name="Owner", value=guild_owner, inline=False)
            embed.add_field(name="Description", value=description, inline=False)
            embed.add_field(name="Member Count", value=member_count, inline=True)
            embed.add_field(name="Guild ID", value=guild_id, inline=True)

            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"An error occurred while fetching the server information: {str(e)}")

def setup(bot):
    bot.add_cog(ServerInfo(bot))
