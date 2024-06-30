import discord
from redbot.core import commands
from yt_dlp import YoutubeDL
import os

class VideoDownloader(commands.Cog):
    """A cog for downloading videos from various platforms."""

    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def download(self, ctx):
        """Group command for downloading videos."""
        pass

    @download.command()
    async def youtube(self, ctx, url: str):
        """Download a video from YouTube."""
        await self.download_video(ctx, url, "youtube")

    @download.command()
    async def tiktok(self, ctx, url: str):
        """Download a video from TikTok."""
        await self.download_video(ctx, url, "tiktok")

    @download.command()
    async def facebook(self, ctx, url: str):
        """Download a video from Facebook."""
        await self.download_video(ctx, url, "facebook")

    @download.command()
    async def instagram(self, ctx, url: str):
        """Download a video from Instagram."""
        await self.download_video(ctx, url, "instagram")

    async def download_video(self, ctx, url: str, platform: str):
        """Download and send a video from the specified platform."""
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'quiet': True
        }

        with YoutubeDL(ydl_opts) as ydl:
            try:
                info_dict = ydl.extract_info(url, download=True)
                video_title = info_dict.get('title', None)
                video_ext = info_dict.get('ext', None)
                video_filename = f"downloads/{video_title}.{video_ext}"

                if os.path.exists(video_filename):
                    await ctx.send(file=discord.File(video_filename))
                    os.remove(video_filename)
                else:
                    await ctx.send("Failed to download the video.")
            except Exception as e:
                await ctx.send(f"An error occurred: {str(e)}")

def setup(bot):
    bot.add_cog(VideoDownloader(bot))
