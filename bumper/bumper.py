import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
from redbot.core.i18n import Translator, set_contextual_locales_from_guild
from discord.ext import tasks
import asyncio
import random
import string

_ = Translator("Bumper", __file__)

class Bumper(commands.Cog):
    """
    A cog for bumping your server to other servers.
    """

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)

        default_guild = {
            "bump_channel": None,
            "invite": None,
            "description": None,
            "embed_color": 0x00FF00,  # Default to green
            "premium": False,
            "last_bump": None
        }

        default_global = {
            "report_channel": None,
            "premium_codes": {},
            "blacklisted_guilds": []
        }

        self.config.register_guild(**default_guild)
        self.config.register_global(**default_global)

        self.reported_bumps = {}
        self.auto_bump_task.start()

    def cog_unload(self):
        self.auto_bump_task.cancel()

    @commands.group()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def bumpset(self, ctx: commands.Context):
        """Group command to set bump configuration."""
        pass

    @bumpset.command()
    async def channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the bump channel."""
        await self.config.guild(ctx.guild).bump_channel.set(channel.id)
        await ctx.send(f"Bump channel set to: {channel.mention}")

    @bumpset.command()
    async def invite(self, ctx: commands.Context, invite: str):
        """Set the invite link."""
        await self.config.guild(ctx.guild).invite.set(invite)
        await ctx.send(f"Invite link set to: {invite}")

    @bumpset.command()
    async def description(self, ctx: commands.Context, *, description: str):
        """Set the server description (max 500 characters)."""
        if len(description) > 500:
            await ctx.send("Description is too long. Please keep it under 500 characters.")
            return
        await self.config.guild(ctx.guild).description.set(description)
        await ctx.send("Description set.")

    @bumpset.command()
    async def embed_color(self, ctx: commands.Context, color: discord.Color):
        """Set the embed color."""
        await self.config.guild(ctx.guild).embed_color.set(color.value)
        await ctx.send(f"Embed color set to: {color}")

    @commands.group()
    @commands.is_owner()
    async def bumpowner(self, ctx: commands.Context):
        """Owner-only bump configuration."""
        pass

    @bumpowner.command()
    async def report_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the channel where bump reports are sent."""
        await self.config.report_channel.set(channel.id)
        await ctx.send(f"Report channel set to: {channel.mention}")

    @bumpowner.command()
    async def generate_code(self, ctx: commands.Context):
        """Generate a premium code."""
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        async with self.config.premium_codes() as premium_codes:
            premium_codes[code] = None
        await ctx.send(f"Generated premium code: {code}")

    @bumpowner.command()
    async def blacklist(self, ctx: commands.Context, guild_id: int):
        """Blacklist a server by ID."""
        async with self.config.blacklisted_guilds() as blacklisted_guilds:
            if guild_id not in blacklisted_guilds:
                blacklisted_guilds.append(guild_id)
                await ctx.send(f"Server with ID {guild_id} has been blacklisted.")
            else:
                await ctx.send(f"Server with ID {guild_id} is already blacklisted.")

    @bumpowner.command()
    async def unblacklist(self, ctx: commands.Context, guild_id: int):
        """Unblacklist a server by ID."""
        async with self.config.blacklisted_guilds() as blacklisted_guilds:
            if guild_id in blacklisted_guilds:
                blacklisted_guilds.remove(guild_id)
                await ctx.send(f"Server with ID {guild_id} has been unblacklisted.")
            else:
                await ctx.send(f"Server with ID {guild_id} is not blacklisted.")

    @commands.command()
    @commands.guild_only()
    async def redeem(self, ctx: commands.Context, code: str):
        """Redeem a premium code."""
        async with self.config.premium_codes() as premium_codes:
            if code in premium_codes and premium_codes[code] is None:
                premium_codes[code] = ctx.guild.id
                await self.config.guild(ctx.guild).premium.set(True)
                await ctx.send("Premium code redeemed! Your server now has premium status.")
            else:
                await ctx.send("Invalid or already used premium code.")

    @commands.command()
    @commands.guild_only()
    async def bump(self, ctx: commands.Context):
        """Send the bump message to all servers with a configured bump channel."""
        await set_contextual_locales_from_guild(self.bot, ctx.guild)

        blacklisted_guilds = await self.config.blacklisted_guilds()
        if ctx.guild.id in blacklisted_guilds:
            await ctx.send("Your server is blacklisted and cannot bump.")
            return

        guild_data = await self.config.guild(ctx.guild).all()
        if not guild_data["bump_channel"] or not guild_data["invite"] or not guild_data["description"]:
            await ctx.send("Please configure all bump settings first using the `bumpset` commands.")
            return

        now = discord.utils.utcnow()
        if guild_data["last_bump"] and (now - guild_data["last_bump"]).total_seconds() < 7200:
            await ctx.send("You can only bump once every 2 hours.")
            return

        await self.send_bump(ctx.guild)

        await self.config.guild(ctx.guild).last_bump.set(now.isoformat())
        await ctx.send("Bump message sent to all configured servers.")

    async def send_bump(self, guild: discord.Guild):
        guild_data = await self.config.guild(guild).all()

        embed = discord.Embed(
            title=f"{guild.name}",
            description=guild_data["description"],
            color=guild_data["embed_color"]
        )
        embed.add_field(name="Invite Link", value=guild_data["invite"], inline=False)
        embed.set_thumbnail(url=guild.icon_url)

        report_button = discord.ui.Button(label="Report", style=discord.ButtonStyle.danger)

        async def report_callback(interaction: discord.Interaction):
            report_channel_id = await self.config.report_channel()
            if not report_channel_id:
                await interaction.response.send_message("Report channel is not configured.", ephemeral=True)
                return

            report_channel = self.bot.get_channel(report_channel_id)
            if not report_channel:
                await interaction.response.send_message("Report channel is not found.", ephemeral=True)
                return

            report_message = await report_channel.send(
                embed=embed,
                content=f"Reported by {interaction.user.mention} from {interaction.guild.name}"
            )
            self.reported_bumps[report_message.id] = (guild.id, interaction.message.id)
            await report_message.add_reaction("✅")
            await report_message.add_reaction("❌")
            await interaction.response.send_message("Bump reported.", ephemeral=True)

        report_button.callback = report_callback

        view = discord.ui.View()
        view.add_item(report_button)

        for g in self.bot.guilds:
            bump_channel_id = await self.config.guild(g).bump_channel()
            if bump_channel_id:
                bump_channel = g.get_channel(bump_channel_id)
                if bump_channel:
                    await bump_channel.send(embed=embed, view=view)

    @tasks.loop(hours=2)
    async def auto_bump_task(self):
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            if await self.config.guild(guild).premium():
                await self.send_bump(guild)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return

        if reaction.message.id not in self.reported_bumps:
            return

        report_channel_id = await self.config.report_channel()
        if reaction.message.channel.id != report_channel_id:
            return

        if reaction.emoji not in ["✅", "❌"]:
            return

        guild_id, message_id = self.reported_bumps[reaction.message.id]
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return

        bump_channel_id = await self.config.guild(guild).bump_channel()
        bump_channel = guild.get_channel(bump_channel_id)
        if not bump_channel:
            return

        bump_message = await bump_channel.fetch_message(message_id)
        if not bump_message:
            return

        if reaction.emoji == "✅":
            await bump_message.delete()
            await reaction.message.channel.send(f"Bump from {guild.name} accepted by {user.mention}.")
        elif reaction.emoji == "❌":
            async with self.config.blacklisted_guilds() as blacklisted_guilds:
                if guild.id not in blacklisted_guilds:
                    blacklisted_guilds.append(guild.id)
            await bump_message.delete()
            await reaction.message.channel.send(f"Bump from {guild.name} denied by {user.mention} and the server has been blacklisted.")

        del self.reported_bumps[reaction.message.id]

def setup(bot: Red):
    bot.add_cog(Bumper(bot))
