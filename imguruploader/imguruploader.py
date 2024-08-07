import discord
from redbot.core import commands, Config
import aiohttp
import io
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("inn.imgur")

class ImgurUploader(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_global(
            imgur_client_id="",
            imgur_client_secret="",
            imgur_access_token=""
        )

    @commands.group()
    async def imgur(self, ctx):
        """Manage Imgur Uploader settings."""
        pass

    @imgur.command()
    async def setid(self, ctx, client_id: str):
        """Set the Imgur client ID."""
        await self.config.imgur_client_id.set(client_id)
        await ctx.send("Imgur client ID has been set.")

    @imgur.command()
    async def setsecret(self, ctx, client_secret: str):
        """Set the Imgur client secret."""
        await self.config.imgur_client_secret.set(client_secret)
        await ctx.send("Imgur client secret has been set.")

    @imgur.command()
    async def setaccess(self, ctx, access_token: str):
        """Set the Imgur access token."""
        await self.config.imgur_access_token.set(access_token)
        await ctx.send("Imgur access token has been set.")

    @imgur.command()
    async def help(self, ctx):
        """Show help for setting up Imgur credentials."""
        help_message = """
        **Imgur Uploader Setup**

        To use the Imgur uploader, you need to set the following credentials:

        1. **Client ID**
        2. **Client Secret**
        3. **Access Token**

        **Commands:**
        - `imgur setid <client_id>`: Set the Imgur client ID.
        - `imgur setsecret <client_secret>`: Set the Imgur client secret.
        - `imgur setaccess <access_token>`: Set the Imgur access token.
        - `imgur upload <name> <description> <attachments>`: Upload images to Imgur with an optional name and description.

        **Getting Imgur Credentials:**

        1. **Client ID and Client Secret:**
           - Go to the [Imgur API](https://api.imgur.com/oauth2/addclient).
           - Log in with your Imgur account.
           - Fill out the form to register your application.
           - After registration, you will receive your Client ID and Client Secret.

        2. **Access Token:**
           - Follow the [Imgur OAuth2 guide](https://apidocs.imgur.com/#authorization-and-oauth) to obtain an access token.
           - Use the Client ID and Client Secret obtained from the previous step.

        Example:
        ```
        imgur setid YOUR_IMGUR_CLIENT_ID
        imgur setsecret YOUR_IMGUR_CLIENT_SECRET
        imgur setaccess YOUR_IMGUR_ACCESS_TOKEN
        imgur upload "Album Name" "Album Description" <attachments>
        ```

        After setting these credentials, you can upload images to Imgur using the `imgur upload` command.
        """
        await ctx.send(help_message)

    @imgur.command()
    async def upload(self, ctx, name: str = "My Album", description: str = "This album contains multiple images."):
        """Upload images to Imgur with an optional name and description."""
        imgur_client_id = await self.config.imgur_client_id()
        imgur_client_secret = await self.config.imgur_client_secret()
        imgur_access_token = await self.config.imgur_access_token()
        if not imgur_client_id or not imgur_client_secret or not imgur_access_token:
            await ctx.send("Imgur client ID, secret, and access token are not set. Please set them using the `imgur setid`, `imgur setsecret`, and `imgur setaccess` commands.")
            logger.error("Imgur credentials are not set.")
            return

        if not ctx.message.attachments:
            await ctx.send("Please attach images to upload.")
            logger.error("No attachments found in the message.")
            return

        image_urls = []
        imgur_image_ids = []
        supported_mime_types = {
            'image/jpeg',
            'image/jpg',
            'image/gif',
            'image/png',
            'image/apng',
            'image/tiff',
            'video/mp4',
            'video/webm',
            'video/x-matroska',
            'video/quicktime',
            'video/x-flv',
            'video/x-msvideo',
            'video/x-ms-wmv',
            'video/mpeg'
        }

        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Client-ID {imgur_client_id}"}

            for attachment in ctx.message.attachments:
                if attachment.content_type in supported_mime_types:
                    async with session.get(attachment.url) as resp:
                        if resp.status != 200:
                            await ctx.send(f"Failed to download file: {attachment.url}")
                            logger.error(f"Failed to download file: {attachment.url}, Status code: {resp.status}")
                            return
                        data = io.BytesIO(await resp.read())

                    async with session.post("https://api.imgur.com/3/image", headers=headers, data={"image": data.read()}) as resp:
                        if resp.status != 200:
                            imgur_response = await resp.json()
                            error_message = imgur_response.get("data", {}).get("error", "Unknown error")
                            await ctx.send(f"Failed to upload file to Imgur: {error_message}")
                            logger.error(f"Failed to upload file to Imgur, Status code: {resp.status}, Error: {error_message}")
                            return
                        imgur_response = await resp.json()
                        image_urls.append(imgur_response["data"]["link"])
                        imgur_image_ids.append(imgur_response["data"]["id"])

        if len(image_urls) == 1:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {imgur_access_token}"}
                data = {
                    "title": name,
                    "description": description
                }
                async with session.post(f"https://api.imgur.com/3/image/{imgur_image_ids[0]}", headers=headers, json=data) as resp:
                    if resp.status != 200:
                        imgur_response = await resp.json()
                        error_message = imgur_response.get("data", {}).get("error", "Unknown error")
                        await ctx.send(f"Failed to set title and description for the image on Imgur: {error_message}")
                        logger.error(f"Failed to set title and description for the image on Imgur, Status code: {resp.status}, Error: {error_message}")
                        return
                    await ctx.send(f"File uploaded to Imgur: {image_urls[0]}")
        elif len(image_urls) > 1:
            headers = {
                "Authorization": f"Bearer {imgur_access_token}",
                "Content-Type": "application/json"
            }
            data = {
                "ids": imgur_image_ids,
                "title": name,
                "description": description
            }

            async with aiohttp.ClientSession() as session:
                async with session.post("https://api.imgur.com/3/album", headers=headers, json=data) as resp:
                    if resp.status != 200:
                        imgur_response = await resp.json()
                        error_message = imgur_response.get("data", {}).get("error", "Unknown error")
                        await ctx.send(f"Failed to create album on Imgur: {error_message}")
                        logger.error(f"Failed to create album on Imgur, Status code: {resp.status}, Error: {error_message}")
                        return
                    album_response = await resp.json()
                    album_link = f"https://imgur.com/a/{album_response['data']['id']}"
                    await ctx.send(f"Album created on Imgur: {album_link}")
