import discord
from redbot.core import commands, Config, checks
from redbot.core.bot import Red

class IntroCog(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        default_guild = {
            "fields": [],
            "intro_channel": None
        }
        self.config.register_guild(**default_guild)
        self.config.register_user(color=None, fields={})

    @commands.guild_only()
    @commands.group()
    async def intro(self, ctx):
        """Manage your introduction."""
        pass

    @intro.command(name="set")
    async def intro_set(self, ctx, color: discord.Color, *, fields: str):
        """Set your introduction.

        Example: [p]intro set #ff0000 name: John Doe, age: 25, hobby: Gaming
        """
        user_data = {field.split(":")[0].strip(): field.split(":")[1].strip() for field in fields.split(",")}
        await self.config.user(ctx.author).color.set(color.value)
        await self.config.user(ctx.author).fields.set(user_data)
        await ctx.send("Your introduction has been set!")

    @intro.command(name="send")
    async def intro_send(self, ctx):
        """Send your introduction to the configured channel."""
        color = await self.config.user(ctx.author).color()
        fields = await self.config.user(ctx.author).fields()
        if not color or not fields:
            await ctx.send("You need to set your introduction first using the `intro set` command.")
            return

        embed = discord.Embed(color=color, title=f"{ctx.author.display_name}'s Introduction")
        for field_name, field_value in fields.items():
            embed.add_field(name=field_name.capitalize(), value=field_value, inline=False)

        intro_channel_id = await self.config.guild(ctx.guild).intro_channel()
        if intro_channel_id:
            intro_channel = self.bot.get_channel(intro_channel_id)
            if intro_channel:
                await intro_channel.send(f"{ctx.author.mention}", embed=embed)
                await ctx.send("Your introduction has been sent!")
            else:
                await ctx.send("The configured introduction channel does not exist.")
        else:
            await ctx.send("The introduction channel has not been set by the server owner or admin.")

    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @intro.command(name="setchannel")
    async def intro_setchannel(self, ctx, channel: discord.TextChannel):
        """Set the channel where introductions will be sent."""
        await self.config.guild(ctx.guild).intro_channel.set(channel.id)
        await ctx.send(f"The introduction channel has been set to {channel.mention}")

    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @intro.command(name="addfield")
    async def intro_addfield(self, ctx, field_name: str):
        """Add a field to the introduction form."""
        fields = await self.config.guild(ctx.guild).fields()
        if field_name not in fields:
            fields.append(field_name)
            await self.config.guild(ctx.guild).fields.set(fields)
            await ctx.send(f"The field `{field_name}` has been added to the introduction form.")
        else:
            await ctx.send(f"The field `{field_name}` already exists in the introduction form.")

    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @intro.command(name="removefield")
    async def intro_removefield(self, ctx, field_name: str):
        """Remove a field from the introduction form."""
        fields = await self.config.guild(ctx.guild).fields()
        if field_name in fields:
            fields.remove(field_name)
            await self.config.guild(ctx.guild).fields.set(fields)
            await ctx.send(f"The field `{field_name}` has been removed from the introduction form.")
        else:
            await ctx.send(f"The field `{field_name}` does not exist in the introduction form.")

def setup(bot: Red):
    bot.add_cog(IntroCog(bot))
