import discord
from redbot.core import commands
from PIL import Image, ImageFilter, ImageOps, ImageEnhance
import aiohttp
import io
import legofy

class ImageManipulation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_image(self, ctx):
        if not ctx.message.attachments:
            await ctx.send("Please attach an image.")
            return None
        attachment = ctx.message.attachments[0]
        img_bytes = await attachment.read()
        return Image.open(io.BytesIO(img_bytes))

    async def send_image(self, ctx, img, filename):
        with io.BytesIO() as image_binary:
            img.save(image_binary, 'PNG')
            image_binary.seek(0)
            await ctx.send(file=discord.File(fp=image_binary, filename=filename))

    @commands.command()
    async def resize(self, ctx, width: int, height: int):
        """Resize an image to the specified width and height."""
        img = await self.get_image(ctx)
        if img:
            img_resized = img.resize((width, height))
            await self.send_image(ctx, img_resized, 'resized.png')

    @commands.command()
    async def rotate(self, ctx, degrees: int):
        """Rotate an image by the specified number of degrees."""
        img = await self.get_image(ctx)
        if img:
            img_rotated = img.rotate(degrees)
            await self.send_image(ctx, img_rotated, 'rotated.png')

    @commands.command()
    async def flip(self, ctx, direction: str):
        """Flip an image. Available directions: horizontal, vertical."""
        img = await self.get_image(ctx)
        if img:
            if direction.lower() == "horizontal":
                img_flipped = ImageOps.mirror(img)
            elif direction.lower() == "vertical":
                img_flipped = ImageOps.flip(img)
            else:
                await ctx.send("Invalid direction. Use 'horizontal' or 'vertical'.")
                return
            await self.send_image(ctx, img_flipped, 'flipped.png')

    @commands.command()
    async def grayscale(self, ctx):
        """Convert an image to grayscale."""
        img = await self.get_image(ctx)
        if img:
            img_gray = ImageOps.grayscale(img)
            await self.send_image(ctx, img_gray, 'grayscale.png')

    @commands.command()
    async def invert(self, ctx):
        """Invert the colors of an image."""
        img = await self.get_image(ctx)
        if img:
            img_inverted = ImageOps.invert(img.convert("RGB"))
            await self.send_image(ctx, img_inverted, 'inverted.png')

    @commands.command()
    async def contrast(self, ctx, factor: float):
        """Adjust the contrast of an image. Factor > 1 increases contrast, < 1 decreases."""
        img = await self.get_image(ctx)
        if img:
            enhancer = ImageEnhance.Contrast(img)
            img_contrast = enhancer.enhance(factor)
            await self.send_image(ctx, img_contrast, 'contrast.png')

    @commands.command()
    async def brightness(self, ctx, factor: float):
        """Adjust the brightness of an image. Factor > 1 increases brightness, < 1 decreases."""
        img = await self.get_image(ctx)
        if img:
            enhancer = ImageEnhance.Brightness(img)
            img_brightness = enhancer.enhance(factor)
            await self.send_image(ctx, img_brightness, 'brightness.png')

    @commands.command()
    async def blur(self, ctx, radius: int):
        """Apply a blur effect to an image."""
        img = await self.get_image(ctx)
        if img:
            img_blurred = img.filter(ImageFilter.GaussianBlur(radius))
            await self.send_image(ctx, img_blurred, 'blurred.png')

    @commands.command()
    async def sharpen(self, ctx, factor: float):
        """Sharpen an image. Factor > 1 increases sharpness, < 1 decreases."""
        img = await self.get_image(ctx)
        if img:
            enhancer = ImageEnhance.Sharpness(img)
            img_sharpen = enhancer.enhance(factor)
            await self.send_image(ctx, img_sharpen, 'sharpen.png')

    @commands.command()
    async def imfilter(self, ctx, filter_name: str):
        """Apply a filter to an image. Available filters: BLUR, CONTOUR, DETAIL, EDGE_ENHANCE, EMBOSS, SHARPEN"""
        img = await self.get_image(ctx)
        if img:
            filter_dict = {
                "BLUR": ImageFilter.BLUR,
                "CONTOUR": ImageFilter.CONTOUR,
                "DETAIL": ImageFilter.DETAIL,
                "EDGE_ENHANCE": ImageFilter.EDGE_ENHANCE,
                "EMBOSS": ImageFilter.EMBOSS,
                "SHARPEN": ImageFilter.SHARPEN
            }

            if filter_name.upper() not in filter_dict:
                await ctx.send("Invalid filter name. Available filters: BLUR, CONTOUR, DETAIL, EDGE_ENHANCE, EMBOSS, SHARPEN")
                return

            img_filtered = img.filter(filter_dict[filter_name.upper()])
            await self.send_image(ctx, img_filtered, 'filtered.png')

    @commands.command()
    async def legofy(self, ctx):
        """Turn an image into a LEGO-style creation."""
        img = await self.get_image(ctx)
        if img:
            legofy.legofy_image(img, img)
            await self.send_image(ctx, img, 'legofy.png')
