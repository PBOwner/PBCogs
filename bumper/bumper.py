import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
from redbot.core.i18n import Translator, set_contextual_locales_from_guild
from discord.ext import tasks
import asyncio
import random
import string
import logging
from datetime import datetime, timezone

_ = Translator("Bumper", __file__)
log = logging.getLogger("red.Bumper")

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
            "last_bump": None,
            "bump_count": 0
        }

        default_global = {
            "report_channel": None,
            "premium_codes": {},
            "blacklisted_guilds": [],
            "trusted_users": []
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
        await ctx.send(embed=discord.Embed(description=f"Bump channel set to: {channel.mention}", color=discord.Color.green()))
        await self.log_new_server_bump(ctx.guild)

    @bumpset.command()
    async def invite(self, ctx: commands.Context, invite: str):
        """Set the invite link."""
        await self.config.guild(ctx.guild).invite.set(invite)
        await ctx.send(embed=discord.Embed(description=f"Invite link set to: {invite}", color=discord.Color.green()))

    @bumpset.command()
    async def description(self, ctx: commands.Context, *, description: str):
        """Set the server description (max 500 characters)."""
        if len(description) > 500:
            await ctx.send(embed=discord.Embed(description="Description is too long. Please keep it under 500 characters.", color=discord.Color.red()))
            return
        await self.config.guild(ctx.guild).description.set(description)
        await ctx.send(embed=discord.Embed(description="Description set.", color=discord.Color.green()))

    @bumpset.command()
    async def embed_color(self, ctx: commands.Context, color: discord.Color):
        """Set the embed color."""
        await self.config.guild(ctx.guild).embed_color.set(color.value)
        await ctx.send(embed=discord.Embed(description=f"Embed color set to: {color}", color=discord.Color.green()))

    @commands.group()
    @commands.is_owner()
    async def bumpowner(self, ctx: commands.Context):
        """Owner-only bump configuration."""
        pass

    @bumpowner.command()
    async def report_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the channel where bump reports are sent."""
        await self.config.report_channel.set(channel.id)
        await ctx.send(embed=discord.Embed(description=f"Report channel set to: {channel.mention}", color=discord.Color.green()))

    @bumpowner.command()
    async def generate_code(self, ctx: commands.Context):
        """Generate a premium code."""
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        async with self.config.premium_codes() as premium_codes:
            premium_codes[code] = None
        await ctx.send(embed=discord.Embed(description=f"Generated premium code: {code}", color=discord.Color.green()))

    @bumpowner.command()
    async def blacklist(self, ctx: commands.Context, guild_id: int):
        """Blacklist a server by ID."""
        async with self.config.blacklisted_guilds() as blacklisted_guilds:
            if guild_id not in blacklisted_guilds:
                blacklisted_guilds.append(guild_id)
                await ctx.send(embed=discord.Embed(description=f"Server with ID {guild_id} has been blacklisted.", color=discord.Color.green()))
            else:
                await ctx.send(embed=discord.Embed(description=f"Server with ID {guild_id} is already blacklisted.", color=discord.Color.orange()))

    @bumpowner.command()
    async def unblacklist(self, ctx: commands.Context, guild_id: int):
        """Unblacklist a server by ID."""
        async with self.config.blacklisted_guilds() as blacklisted_guilds:
            if guild_id in blacklisted_guilds:
                blacklisted_guilds.remove(guild_id)
                await ctx.send(embed=discord.Embed(description=f"Server with ID {guild_id} has been unblacklisted.", color=discord.Color.green()))
            else:
                await ctx.send(embed=discord.Embed(description=f"Server with ID {guild_id} is not blacklisted.", color=discord.Color.orange()))

    @bumpowner.command()
    async def add_trusted(self, ctx: commands.Context, user: discord.User):
        """Add a trusted user to accept or deny reports."""
        async with self.config.trusted_users() as trusted_users:
            if user.id not in trusted_users:
                trusted_users.append(user.id)
                await ctx.send(embed=discord.Embed(description=f"User {user.mention} has been added as a trusted user.", color=discord.Color.green()))
            else:
                await ctx.send(embed=discord.Embed(description=f"User {user.mention} is already a trusted user.", color=discord.Color.orange()))

    @bumpowner.command()
    async def remove_trusted(self, ctx: commands.Context, user: discord.User):
        """Remove a trusted user."""
        async with self.config.trusted_users() as trusted_users:
            if user.id in trusted_users:
                trusted_users.remove(user.id)
                await ctx.send(embed=discord.Embed(description=f"User {user.mention} has been removed from trusted users.", color=discord.Color.green()))
            else:
                await ctx.send(embed=discord.Embed(description=f"User {user.mention} is not a trusted user.", color=discord.Color.orange()))

    @commands.command()
    @commands.guild_only()
    async def redeem(self, ctx: commands.Context, code: str):
        """Redeem a premium code."""
        async with self.config.premium_codes() as premium_codes:
            if code in premium_codes and premium_codes[code] is None:
                premium_codes[code] = ctx.guild.id
                await self.config.guild(ctx.guild).premium.set(True)
                await ctx.send(embed=discord.Embed(description="Premium code redeemed! Your server now has premium status.", color=discord.Color.green()))
            else:
                await ctx.send(embed=discord.Embed(description="Invalid or already used premium code.", color=discord.Color.red()))

    @commands.command()
    @commands.guild_only()
    async def bumper(self, ctx: commands.Context):
        """Send the bump message to all servers with a configured bump channel."""
        await set_contextual_locales_from_guild(self.bot, ctx.guild)

        blacklisted_guilds = await self.config.blacklisted_guilds()
        if ctx.guild.id in blacklisted_guilds:
            await ctx.send(embed=discord.Embed(description="Your server is blacklisted and cannot bump.", color=discord.Color.red()))
            return

        guild_data = await self.config.guild(ctx.guild).all()
        if not guild_data["bump_channel"] or not guild_data["invite"] or not guild_data["description"]:
            await ctx.send(embed=discord.Embed(description="Please configure all bump settings first using the `bumpset` commands.", color=discord.Color.red()))
            return

        now = datetime.now(timezone.utc)
        if guild_data["last_bump"]:
            last_bump = datetime.fromisoformat(guild_data["last_bump"])
            if (now - last_bump).total_seconds() < 7200 and not await self.bot.is_owner(ctx.author):
                await ctx.send(embed=discord.Embed(description="You can only bump once every 2 hours.", color=discord.Color.red()))
                return

        await self.send_bump(ctx.guild)

        await self.config.guild(ctx.guild).last_bump.set(now.isoformat())
        await self.increment_bump_count(ctx.guild)
        await ctx.send(embed=discord.Embed(description="Bump message sent to all configured servers.", color=discord.Color.green()))

    async def send_bump(self, guild: discord.Guild):
        guild_data = await self.config.guild(guild).all()

        embed = discord.Embed(
            title=f"{guild.name}",
            description=guild_data["description"],
            color=guild_data["embed_color"]
        )
        embed.add_field(name="Invite Link", value=guild_data["invite"], inline=False)

        report_button = discord.ui.Button(label="Report", style=discord.ButtonStyle.danger)

        async def report_callback(interaction: discord.Interaction):
            report_channel_id = await self.config.report_channel()
            if not report_channel_id:
                await interaction.response.send_message(embed=discord.Embed(description="Report channel is not configured.", color=discord.Color.red()), ephemeral=True)
                return

            report_channel = self.bot.get_channel(report_channel_id)
            if not report_channel:
                await interaction.response.send_message(embed=discord.Embed(description="Report channel is not found.", color=discord.Color.red()), ephemeral=True)
                return

            report_message = await report_channel.send(
                embed=embed,
                content=f"Reported by {interaction.user.mention} from {interaction.guild.name}"
            )
            self.reported_bumps[report_message.id] = (guild.id, interaction.message.id)
            await interaction.response.send_message(embed=discord.Embed(description="Bump reported.", color=discord.Color.green()), ephemeral=True)

        report_button.callback = report_callback

        view = discord.ui.View()
        view.add_item(report_button)

        log.info(f"Sending bump from {guild.name} to all configured servers.")

        for g in self.bot.guilds:
            bump_channel_id = await self.config.guild(g).bump_channel()
            if bump_channel_id:
                bump_channel = g.get_channel(bump_channel_id)
                if bump_channel:
                    await bump_channel.send(embed=embed, view=view)
                    log.info(f"Bump sent to {g.name} in channel {bump_channel.name}.")
                    await self.log_bump(g, guild)

    @commands.group()
    @commands.is_owner()
    async def bumprep(self, ctx: commands.Context):
        """Group command for handling bump reports."""
        pass

    @bumprep.command()
    async def accept(self, ctx: commands.Context, report_message_id: int):
        """Accept a reported bump."""
        trusted_users = await self.config.trusted_users()
        if ctx.author.id not in trusted_users and not await self.bot.is_owner(ctx.author):
            await ctx.send(embed=discord.Embed(description="You are not authorized to accept bump reports.", color=discord.Color.red()))
            return

        report_channel_id = await self.config.report_channel()
        report_channel = self.bot.get_channel(report_channel_id)
        if not report_channel:
            await ctx.send(embed=discord.Embed(description="Report channel is not configured or found.", color=discord.Color.red()))
            return

        try:
            report_message = await report_channel.fetch_message(report_message_id)
        except discord.NotFound:
            await ctx.send(embed=discord.Embed(description="Report message not found.", color=discord.Color.red()))
            return

        guild_id, message_id = self.reported_bumps.pop(report_message_id, (None, None))
        if not guild_id:
            await ctx.send(embed=discord.Embed(description="Report not found in the system.", color=discord.Color.red()))
            return

        guild = self.bot.get_guild(guild_id)
        if not guild:
            await ctx.send(embed=discord.Embed(description="Guild not found.", color=discord.Color.red()))
            return

        bump_channel_id = await self.config.guild(guild).bump_channel()
        bump_channel = guild.get_channel(bump_channel_id)
        if not bump_channel:
            await ctx.send(embed=discord.Embed(description="Bump channel not found.", color=discord.Color.red()))
            return

        try:
            bump_message = await bump_channel.fetch_message(message_id)
            await bump_message.delete()
            async with self.config.blacklisted_guilds() as blacklisted_guilds:
                if guild.id not in blacklisted_guilds:
                    blacklisted_guilds.append(guild.id)
            await ctx.send(embed=discord.Embed(description=f"Bump from {guild.name} accepted and the server has been blacklisted.", color=discord.Color.green()))
        except discord.NotFound:
            await ctx.send(embed=discord.Embed(description="Bump message not found in the bump channel.", color=discord.Color.red()))

        await report_message.delete()

    @bumprep.command()
    async def deny(self, ctx: commands.Context, report_message_id: int):
        """Deny a reported bump."""
        trusted_users = await self.config.trusted_users()
        if ctx.author.id not in trusted_users and not await self.bot.is_owner(ctx.author):
            await ctx.send(embed=discord.Embed(description="You are not authorized to deny bump reports.", color=discord.Color.red()))
            return

        report_channel_id = await self.config.report_channel()
        report_channel = self.bot.get_channel(report_channel_id)
        if not report_channel:
            await ctx.send(embed=discord.Embed(description="Report channel is not configured or found.", color=discord.Color.red()))
            return

        try:
            report_message = await report_channel.fetch_message(report_message_id)
        except discord.NotFound:
            await ctx.send(embed=discord.Embed(description="Report message not found.", color=discord.Color.red()))
            return

        self.reported_bumps.pop(report_message_id, None)
        await ctx.send(embed=discord.Embed(description="Report denied and dismissed.", color=discord.Color.green()))

        await report_message.delete()

    @tasks.loop(hours=2)
    async def auto_bump_task(self):
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            if await self.config.guild(guild).premium():
                log.info(f"Auto bumping for premium guild: {guild.name}")
                await self.send_bump(guild)

    async def increment_bump_count(self, guild: discord.Guild):
        current_count = await self.config.guild(guild).bump_count()
        await self.config.guild(guild).bump_count.set(current_count + 1)
        bump_channel_id = await self.config.guild(guild).bump_channel()
        bump_channel = guild.get_channel(bump_channel_id)
        if bump_channel:
            await bump_channel.send(f"{guild.name} was bumped by {guild.owner.name}. This server has been bumped {current_count + 1} times.")

    async def log_bump(self, target_guild: discord.Guild, source_guild: discord.Guild):
        bump_count = await self.config.guild(source_guild).bump_count()
        bump_channel_id = await self.config.guild(target_guild).bump_channel()
        bump_channel = target_guild.get_channel(bump_channel_id)
        if bump_channel:
            await bump_channel.send(f"{source_guild.name} was bumped by {source_guild.owner.name}. This server has been bumped {bump_count} times.")

    async def log_new_server_bump(self, guild: discord.Guild):
        report_channel_id = await self.config.report_channel()
        if not report_channel_id:
            return
        report_channel = self.bot.get_channel(report_channel_id)
        if not report_channel:
            return
        embed = discord.Embed(title="New Server Bump", color=discord.Color.blue())
        embed.add_field(name="Server Name", value=guild.name, inline=True)
        embed.add_field(name="Server ID", value=guild.id, inline=True)
        embed.add_field(name="Server Owner", value=guild.owner.name, inline=True)
        embed.add_field(name="Server Owner ID", value=guild.owner.id, inline=True)
        await report_channel.send(embed=embed)
