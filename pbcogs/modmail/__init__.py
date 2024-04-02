import discord
from discord.ext import commands
from .modmail import ModMail

async def setup(bot):
    await bot.add_cog(ModMail(bot))
    print("ModMail cog loaded successfully!")
