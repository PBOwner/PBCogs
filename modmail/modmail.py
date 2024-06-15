import discord
from discord.ext import commands
from redbot.core import Config
import asyncio
from redbot.core import commands

class Modmail(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)  # Unique identifier for the config
        default_guild = {
            "modmail_channel_id": None,
            "snippets": {}
        }
        self.config.register_guild(**default_guild)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        
        if not message.guild:
            modmail_channel_id = await self.config.guild(message.guild).modmail_channel_id()
            if modmail_channel_id:
                modmail_channel = self.bot.get_channel(modmail_channel_id)
                if modmail_channel and message.channel.id != modmail_channel_id:
                    await modmail_channel.send(f"**{message.author}** from DMs: {message.content}")
    
    @commands.command()
    async def set_modmail_channel(self, ctx, channel: discord.TextChannel):
        """Set the modmail channel for receiving messages."""
        await self.config.guild(ctx.guild).modmail_channel_id.set(channel.id)
        await ctx.send(f"Modmail channel set to {channel.mention}.")
    
    @commands.command()
    async def modmail_reply(self, ctx, *, reply):
        """Reply to a modmail message."""
        modmail_channel_id = await self.config.guild(ctx.guild).modmail_channel_id()
        if modmail_channel_id:
            modmail_channel = self.bot.get_channel(modmail_channel_id)
            if modmail_channel and ctx.channel.id != modmail_channel_id:
                await modmail_channel.send(f"**{ctx.author}**: {reply}")
                await ctx.send("Your reply has been sent.")
            else:
                await ctx.send("Modmail channel is not set or invalid.")
        else:
            await ctx.send("Modmail channel is not set. Please set a modmail channel first.")
    
    @commands.command()
    async def ar(self, ctx, *, reply):
        """Reply to a modmail message anonymously."""
        modmail_channel_id = await self.config.guild(ctx.guild).modmail_channel_id()
        if modmail_channel_id:
            modmail_channel = self.bot.get_channel(modmail_channel_id)
            if modmail_channel and ctx.channel.id == modmail_channel_id:
                embed = discord.Embed(description=reply, color=0x00ff00)
                await ctx.send("Your anonymous reply has been sent.")
                await ctx.author.send(embed=embed)
            else:
                await ctx.send("You can only use this command in the modmail channel.")
        else:
            await ctx.send("Modmail channel is not set. Please set a modmail channel first.")
    
    @commands.group()
    async def snippet(self, ctx):
        """Manage snippets for modmail."""
        pass
    
    @snippet.command()
    async def add(self, ctx, name, content):
        """Add a new snippet."""
        snippets = await self.config.guild(ctx.guild).snippets()
        snippets[name] = content
        await self.config.guild(ctx.guild).snippets.set(snippets)
        await ctx.send(f"Snippet '{name}' added.")
    
    @snippet.command()
    async def edit(self, ctx, name, content):
        """Edit an existing snippet."""
        snippets = await self.config.guild(ctx.guild).snippets()
        if name in snippets:
            snippets[name] = content
            await self.config.guild(ctx.guild).snippets.set(snippets)
            await ctx.send(f"Snippet '{name}' edited.")
        else:
            await ctx.send(f"Snippet '{name}' does not exist.")
    
    @snippet.command()
    async def delete(self, ctx, name):
        """Delete a snippet."""
        snippets = await self.config.guild(ctx.guild).snippets()
        if name in snippets:
            del snippets[name]
            await self.config.guild(ctx.guild).snippets.set(snippets)
            await ctx.send(f"Snippet '{name}' deleted.")
        else:
            await ctx.send(f"Snippet '{name}' does not exist.")
    
    @commands.command()
    async def close(self, ctx, reason: str, time_until_close: int):
        """Close the modmail thread with a reason and specified time until closure."""
        modmail_channel_id = await self.config.guild(ctx.guild).modmail_channel_id()
        if modmail_channel_id:
            modmail_channel = self.bot.get_channel(modmail_channel_id)
            if modmail_channel and ctx.channel.id == modmail_channel_id:
                await ctx.send(f"The modmail thread will be closed in {time_until_close} seconds with reason: {reason}")
                await asyncio.sleep(time_until_close)
                await modmail_channel.send(f"The modmail thread has been closed. Reason: {reason}")
                await ctx.channel.delete()
            else:
                await ctx.send("You can only use this command in the modmail channel.")
        else:
            await ctx.send("Modmail channel is not set. Please set a modmail channel first.")
    
    @commands.command()
    async def rename_thread(self, ctx, new_name):
        """Rename the modmail thread."""
        modmail_channel_id = await self.config.guild(ctx.guild).modmail_channel_id()
        if modmail_channel_id:
            modmail_channel = self.bot.get_channel(modmail_channel_id)
            if modmail_channel and ctx.channel.id == modmail_channel_id:
                await modmail_channel.edit(name=new_name)
                await ctx.send(f"The modmail thread has been renamed to '{new_name}'.")
            else:
                await ctx.send("You can only use this command in the modmail channel.")
        else:
            await ctx.send("Modmail channel is not set. Please set a modmail channel first.")
    
    @commands.command()
    async def move_thread(self, ctx, category: discord.CategoryChannel):
        """Move the modmail thread to a different category."""
        modmail_channel_id = await self.config.guild(ctx.guild).modmail_channel_id()
        if modmail_channel_id:
            modmail_channel = self.bot.get_channel(modmail_channel_id)
            if modmail_channel and ctx.channel.id == modmail_channel_id:
                await modmail_channel.edit(category=category)
                await ctx.send(f"The modmail thread has been moved to the category '{category}'.")
            else:
                await ctx.send("You can only use this command in the modmail channel.")
        else:
            await ctx.send("Modmail channel is not set. Please set a modmail channel first.")

def setup(bot):
    bot.add_cog(Modmail(bot))
