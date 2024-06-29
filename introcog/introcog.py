import discord
from redbot.core import commands, Config, checks
from redbot.core.bot import Red

class IntroCog(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        default_guild = {
            "fields": [],
            "intro_channel": None,
            "title": "Introduction",  # Default title
            "footer": None,  # Default footer
            "break_field_title": None  # Default break field title
        }
        default_user = {
            "color": None,
            "fields": {},
            "last_intro_message_id": None
        }
        self.config.register_guild(**default_guild)
        self.config.register_user(**default_user)

    @commands.guild_only()
    @commands.group()
    async def intro(self, ctx):
        """Manage your introduction."""
        pass

    @intro.command(name="setcolor")
    async def intro_setcolor(self, ctx, color: discord.Color):
        """Set the color for your introduction embed."""
        await self.config.user(ctx.author).color.set(color.value)
        await ctx.send(f"Your introduction color has been set to {color}!")

    @intro.command(name="addvalue")
    async def intro_addvalue(self, ctx, field_name: str, *, field_value: str):
        """Add a field value to your introduction.

        Example: [p]intro addvalue name John Doe
        """
        fields = await self.config.user(ctx.author).fields()
        fields[field_name] = field_value
        await self.config.user(ctx.author).fields.set(fields)
        await ctx.send(f"Field `{field_name}` has been set to `{field_value}` in your introduction.")

    @intro.command(name="removevalue")
    async def intro_removevalue(self, ctx, field_name: str):
        """Remove a field value from your introduction."""
        fields = await self.config.user(ctx.author).fields()
        if field_name in fields:
            del fields[field_name]
            await self.config.user(ctx.author).fields.set(fields)
            await ctx.send(f"Field `{field_name}` has been removed from your introduction.")
        else:
            await ctx.send(f"Field `{field_name}` does not exist in your introduction.")

    @intro.command(name="editvalue")
    async def intro_editvalue(self, ctx, field_name: str, *, field_value: str):
        """Edit a field value in your introduction.

        Example: [p]intro editvalue name Jane Doe
        """
        fields = await self.config.user(ctx.author).fields()
        if field_name in fields:
            fields[field_name] = field_value
            await self.config.user(ctx.author).fields.set(fields)
            await ctx.send(f"Field `{field_name}` has been updated to `{field_value}` in your introduction.")
        else:
            await ctx.send(f"Field `{field_name}` does not exist in your introduction. Use `intro addvalue` to add it first.")

    @intro.command(name="viewfields")
    async def intro_viewfields(self, ctx):
        """View the fields available for your introduction in this server."""
        fields = await self.config.guild(ctx.guild).fields()
        if not fields:
            await ctx.send("No fields have been added to the introduction form for this server.")
            return

        embed = discord.Embed(
            title="Available Fields for Introduction",
            description="The following fields are available for your introduction in this server:",
            color=discord.Color.blue()
        )

        for field in fields:
            embed.add_field(name=field.capitalize(), value=f"Use `[p]intro addvalue {field} <value>` to set this field.", inline=False)

        await ctx.send(embed=embed)

    @intro.command(name="preview")
    async def intro_preview(self, ctx):
        """Preview your introduction."""
        color = await self.config.user(ctx.author).color()
        fields = await self.config.user(ctx.author).fields()
        title = await self.config.guild(ctx.guild).title()
        footer = await self.config.guild(ctx.guild).footer()
        break_field_title = await self.config.guild(ctx.guild).break_field_title()
        if not color or not fields:
            await ctx.send("You need to set your introduction color and fields first.")
            return

        embed = discord.Embed(color=color, title=title)
        for field_name, field_value in fields.items():
            embed.add_field(name=field_name.capitalize(), value=field_value, inline=False)

        if break_field_title:
            embed.add_field(name=break_field_title, value="\u200b", inline=False)

        if footer:
            embed.set_footer(text=footer)

        await ctx.send(embed=embed)

    @intro.command(name="send")
    async def intro_send(self, ctx):
        """Send your introduction to the configured channel."""
        color = await self.config.user(ctx.author).color()
        fields = await self.config.user(ctx.author).fields()
        title = await self.config.guild(ctx.guild).title()
        footer = await self.config.guild(ctx.guild).footer()
        break_field_title = await self.config.guild(ctx.guild).break_field_title()
        if not color or not fields:
            await ctx.send("You need to set your introduction color and fields first.")
            return

        embed = discord.Embed(color=color, title=title)
        for field_name, field_value in fields.items():
            embed.add_field(name=field_name.capitalize(), value=field_value, inline=False)

        if break_field_title:
            embed.add_field(name=break_field_title, value="\u200b", inline=False)

        if footer:
            embed.set_footer(text=footer)

        intro_channel_id = await self.config.guild(ctx.guild).intro_channel()
        if intro_channel_id:
            intro_channel = self.bot.get_channel(intro_channel_id)
            if intro_channel:
                last_intro_message_id = await self.config.user(ctx.author).last_intro_message_id()
                if last_intro_message_id:
                    try:
                        last_intro_message = await intro_channel.fetch_message(last_intro_message_id)
                        await last_intro_message.delete()
                    except discord.NotFound:
                        pass

                new_intro_message = await intro_channel.send(f"{ctx.author.mention}", embed=embed)
                await self.config.user(ctx.author).last_intro_message_id.set(new_intro_message.id)
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

    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @intro.command(name="settitle")
    async def intro_settitle(self, ctx, *, title: str):
        """Set the title for the introduction embed."""
        await self.config.guild(ctx.guild).title.set(title)
        await ctx.send(f"The introduction title has been set to `{title}`.")

    @intro.command(name="viewtitle")
    async def intro_viewtitle(self, ctx):
        """View the current title for the introduction embed."""
        title = await self.config.guild(ctx.guild).title()
        await ctx.send(f"The current introduction title is `{title}`.")

    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @intro.command(name="setfooter")
    async def intro_setfooter(self, ctx, *, footer: str):
        """Set the footer for the introduction embed."""
        await self.config.guild(ctx.guild).footer.set(footer)
        await ctx.send(f"The introduction footer has been set to `{footer}`.")

    @intro.command(name="viewfooter")
    async def intro_viewfooter(self, ctx):
        """View the current footer for the introduction embed."""
        footer = await self.config.guild(ctx.guild).footer()
        await ctx.send(f"The current introduction footer is `{footer}`.")

    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @intro.command(name="setbreakfield")
    async def intro_setbreakfield(self, ctx, *, break_field_title: str):
        """Set the title for the break field."""
        await self.config.guild(ctx.guild).break_field_title.set(break_field_title)
        await ctx.send(f"The break field title has been set to `{break_field_title}`.")

    @intro.command(name="viewbreakfield")
    async def intro_viewbreakfield(self, ctx):
        """View the current break field title."""
        break_field_title = await self.config.guild(ctx.guild).break_field_title()
        await ctx.send(f"The current break field title is `{break_field_title}`.")

    @intro.command(name="example")
    async def intro_example(self, ctx):
        """Set an example introduction with predefined fields and values."""
        example_fields = {f"Example field {i}": "Example Description" for i in range(1, 16)}
        example_title = "Example Title"
        example_footer = "Example Footer"
        example_break_field_title = "Example Break Field"
        await self.config.user(ctx.author).color.set(discord.Color.blue().value)
        await self.config.user(ctx.author).fields.set(example_fields)
        await self.config.guild(ctx.guild).title.set(example_title)
        await self.config.guild(ctx.guild).footer.set(example_footer)
        await self.config.guild(ctx.guild).break_field_title.set(example_break_field_title)
        await ctx.send("Example introduction has been set with predefined fields, title, footer, and break field title.")
