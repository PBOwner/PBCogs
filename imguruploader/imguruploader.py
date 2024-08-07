import discord
from redbot.core import commands, Config
import aiohttp
import io

class ImgurUploader(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_global(
            imgur_client_id="",
            upload_channel_id=None
        )

    @commands.group()
    async def imguruploader(self, ctx):
        """Manage Imgur Uploader settings."""
        pass

    @imguruploader.command()
    async def setclientid(self, ctx, client_id: str):
        """Set the Imgur client ID."""
        await self.config.imgur_client_id.set(client_id)
        await ctx.send("Imgur client ID has been set.")

    @imguruploader.command()
    async def setchannel(self, ctx, channel: discord.TextChannel):
        """Set the channel for automatic uploads."""
        await self.config.upload_channel_id.set(channel.id)
        await ctx.send(f"Channel {channel.mention} has been set for automatic uploads.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        upload_channel_id = await self.config.upload_channel_id()
        if not upload_channel_id or message.channel.id != upload_channel_id:
            return

        imgur_client_id = await self.config.imgur_client_id()
        if not imgur_client_id:
            await message.channel.send("Imgur client ID is not set. Please set it using the `imguruploader setclientid` command.")
            return

        image_urls = []

        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Client-ID {imgur_client_id}"}

            for attachment in message.attachments:
                if attachment.filename.lower().endswith(('png', 'jpg', 'jpeg', 'gif', 'bmp', 'pdf')):
                    async with session.get(attachment.url) as resp:
                        if resp.status != 200:
                            await message.channel.send(f"Failed to download file: {attachment.url}")
                            return
                        data = io.BytesIO(await resp.read())

                    async with session.post("https://api.imgur.com/3/image", headers=headers, data={"image": data.read()}) as resp:
                        if resp.status != 200:
                            await message.channel.send("Failed to upload file to Imgur.")
                            return
                        imgur_response = await resp.json()
                        image_urls.append(imgur_response["data"]["link"])

        if len(image_urls) == 1:
            await message.channel.send(f"File uploaded to Imgur: {image_urls[0]}")
        elif len(image_urls) > 1:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Client-ID {imgur_client_id}"}
                data = {"ids": ",".join(image_urls)}
                async with session.post("https://api.imgur.com/3/album", headers=headers, data=data) as resp:
                    if resp.status != 200:
                        await message.channel.send("Failed to create album on Imgur.")
                        return
                    album_response = await resp.json()

            album_link = f"https://imgur.com/a/{album_response['data']['id']}"
            await message.channel.send(f"Album created on Imgur: {album_link}")
        else:
            await message.channel.send("No valid files were provided.")
