import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
from datetime import datetime

class AdvancedInviteTracker(commands.Cog):
    """Advanced Invite Tracker Cog"""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567892, force_registration=True)
        default_guild = {
            "invites": {},
            "invite_counts": {},
            "log_channel": None,
            "variables": {}
        }
        self.config.register_guild(**default_guild)
        self.invites_cache = {}

    async def initialize(self):
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            try:
                self.invites_cache[guild.id] = await guild.invites()
            except discord.Forbidden:
                print(f"Missing permissions to fetch invites for guild: {guild.name} ({guild.id})")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        invites_before = self.invites_cache.get(member.guild.id, [])
        invites_after = await member.guild.invites()
        self.invites_cache[member.guild.id] = invites_after

        invite_used = None
        for invite in invites_before:
            if invite.uses < next((i.uses for i in invites_after if i.code == invite.code), invite.uses):
                invite_used = invite
                break

        if invite_used:
            inviter_id = str(invite_used.inviter.id)
            async with self.config.guild(member.guild).invites() as invites:
                if inviter_id not in invites:
                    invites[inviter_id] = []
                invites[inviter_id].append(member.id)

            async with self.config.guild(member.guild).invite_counts() as invite_counts:
                if inviter_id not in invite_counts:
                    invite_counts[inviter_id] = {"joined": 0, "left": 0}
                invite_counts[inviter_id]["joined"] += 1

            await self.send_invite_embed(member, invite_used.inviter, "joined")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        async with self.config.guild(member.guild).invites() as invites:
            for inviter_id, invitees in invites.items():
                if member.id in invitees:
                    invitees.remove(member.id)
                    async with self.config.guild(member.guild).invite_counts() as invite_counts:
                        if inviter_id not in invite_counts:
                            invite_counts[inviter_id] = {"joined": 0, "left": 0}
                        invite_counts[inviter_id]["left"] += 1
                    inviter = member.guild.get_member(int(inviter_id))
                    await self.send_invite_embed(member, inviter, "left")
                    break

    async def send_invite_embed(self, member, inviter, action):
        if not inviter:
            return
        embed = discord.Embed(
            title=f"User {action.capitalize()}",
            description=f"{member.mention} has {action} the server.",
            color=discord.Color.green() if action == "joined" else discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Invited By", value=inviter.mention)
        embed.set_footer(text=f"User ID: {member.id}")
        log_channel_id = await self.config.guild(member.guild).log_channel()
        if log_channel_id:
            log_channel = member.guild.get_channel(log_channel_id)
            if log_channel:
                await log_channel.send(embed=embed)

    @commands.group()
    async def invites(self, ctx):
        """Invite tracking commands"""
        pass

    @invites.command(name="add-invites")
    @commands.admin_or_permissions(manage_guild=True)
    async def add_invites(self, ctx, inviter: discord.Member, invite_code: str):
        """Add a new invite to the tracker."""
        async with self.config.guild(ctx.guild).invites() as invites:
            invites.setdefault(str(inviter.id), []).append(invite_code)
        await ctx.send(f"Invite `{invite_code}` added for {inviter.mention}.")

    @invites.command(name="reset-invites")
    @commands.admin_or_permissions(manage_guild=True)
    async def reset_invites(self, ctx):
        """Reset the invite tracker."""
        await self.config.guild(ctx.guild).invites.clear()
        await self.config.guild(ctx.guild).invite_counts.clear()
        await ctx.send("Invite tracker has been reset.")

    @invites.command(name="invites")
    async def view_invites(self, ctx, member: discord.Member = None):
        """View the current invite tracker."""
        member = member or ctx.author
        invites = await self.config.guild(ctx.guild).invites()
        invite_counts = await self.config.guild(ctx.guild).invite_counts()
        inviter_id = str(member.id)
        if inviter_id in invites:
            embed = discord.Embed(
                title=f"Invites for {member.display_name}",
                color=discord.Color.blue()
            )
            embed.add_field(name="Total Invites", value=len(invites[inviter_id]))
            embed.add_field(name="Joined", value=invite_counts.get(inviter_id, {}).get("joined", 0))
            embed.add_field(name="Left", value=invite_counts.get(inviter_id, {}).get("left", 0))
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"{member.mention} has no invites tracked.")

    @invites.command(name="delete-invite")
    @commands.admin_or_permissions(manage_guild=True)
    async def delete_invite(self, ctx, inviter: discord.Member, invite_code: str):
        """Delete a specific invite from the tracker."""
        async with self.config.guild(ctx.guild).invites() as invites:
            inviter_id = str(inviter.id)
            if inviter_id in invites and invite_code in invites[inviter_id]:
                invites[inviter_id].remove(invite_code)
                await ctx.send(f"Invite `{invite_code}` removed for {inviter.mention}.")
            else:
                await ctx.send(f"{inviter.mention} does not have invite `{invite_code}` tracked.")

    @invites.command(name="leaderboard")
    async def invite_leaderboard(self, ctx):
        """View the leaderboard for top inviters in your server."""
        invite_counts = await self.config.guild(ctx.guild).invite_counts()
        sorted_invites = sorted(invite_counts.items(), key=lambda x: x[1]["joined"] - x[1]["left"], reverse=True)
        pages = []
        page = []
        for i, (inviter_id, counts) in enumerate(sorted_invites, 1):
            inviter = ctx.guild.get_member(int(inviter_id))
            if not inviter:
                continue
            joined = counts["joined"]
            left = counts["left"]
            net = joined - left
            page.append(f"{i}. {inviter.mention} - Invites: {net} (Joined: {joined}, Left: {left})")
            if len(page) == 10:
                pages.append("\n".join(page))
                page = []
        if page:
            pages.append("\n".join(page))

        for i, page in enumerate(pages, 1):
            embed = discord.Embed(
                title=f"Invite Leaderboard - Page {i}/{len(pages)}",
                description=page,
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)

    @invites.command(name="ping")
    async def ping(self, ctx):
        """Ping the bot to check its availability."""
        await ctx.send(f"Pong! {round(self.bot.latency * 1000)}ms")

    @invites.command(name="roleinfo")
    async def role_info(self, ctx, role: discord.Role):
        """View information about a specific role in your server."""
        embed = discord.Embed(
            title=f"Role Info - {role.name}",
            color=role.color,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="ID", value=role.id)
        embed.add_field(name="Color", value=str(role.color))
        embed.add_field(name="Position", value=role.position)
        embed.add_field(name="Mentionable", value=role.mentionable)
        embed.add_field(name="Permissions", value=", ".join(perm[0] for perm in role.permissions if perm[1]))
        await ctx.send(embed=embed)

    @invites.command(name="serverinfo")
    async def server_info(self, ctx):
        """View information about your server."""
        guild = ctx.guild
        embed = discord.Embed(
            title=f"Server Info - {guild.name}",
            description=guild.description or "No description",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.add_field(name="ID", value=guild.id)
        embed.add_field(name="Owner", value=guild.owner.mention)
        embed.add_field(name="Members", value=guild.member_count)
        embed.add_field(name="Roles", value=len(guild.roles))
        embed.add_field(name="Channels", value=len(guild.channels))
        embed.add_field(name="Created At", value=guild.created_at.strftime("%Y-%m-%d %H:%M:%S"))
        await ctx.send(embed=embed)

    @invites.command(name="stats")
    async def stats(self, ctx):
        """View statistics about your server, including invite tracking."""
        guild = ctx.guild
        invite_counts = await self.config.guild(guild).invite_counts()
        total_invites = sum(counts["joined"] for counts in invite_counts.values())
        total_left = sum(counts["left"] for counts in invite_counts.values())
        net_invites = total_invites - total_left
        embed = discord.Embed(
            title=f"Server Stats - {guild.name}",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Total Invites", value=total_invites)
        embed.add_field(name="Total Left", value=total_left)
        embed.add_field(name="Net Invites", value=net_invites)
        embed.add_field(name="Members", value=guild.member_count)
        await ctx.send(embed=embed)

    @invites.command(name="support")
    async def support(self, ctx):
        """Get help and support from the Invite Tracker team."""
        embed = discord.Embed(
            title="Invite Tracker Support",
            description="For support, please visit our [support server](https://discord.gg/DmGBCrRtQz).",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        await ctx.send(embed=embed)

    @invites.command(name="userinfo")
    async def user_info(self, ctx, member: discord.Member):
        """View information about a specific user in your server."""
        embed = discord.Embed(
            title=f"User Info - {member.display_name}",
            color=member.color,
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
        embed.add_field(name="ID", value=member.id)
        embed.add_field(name="Joined At", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"))
        embed.add_field(name="Created At", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S"))
        embed.add_field(name="Roles", value=", ".join(role.mention for role in member.roles if role != ctx.guild.default_role))
        await ctx.send(embed=embed)

    @invites.command(name="variables")
    @commands.admin_or_permissions(manage_guild=True)
    async def variables(self, ctx, action: str, key: str = None, value: str = None):
        """View and manage variables for the Invite Tracker bot."""
        if action == "view":
            variables = await self.config.guild(ctx.guild).variables()
            if key:
                if key in variables:
                    await ctx.send(f"Variable `{key}`: {variables[key]}")
                else:
                    await ctx.send(f"Variable `{key}` not found.")
            else:
                embed = discord.Embed(
                    title="Invite Tracker Variables",
                    color=discord.Color.blue()
                )
                for k, v in variables.items():
                    embed.add_field(name=k, value=v)
                await ctx.send(embed=embed)
        elif action == "set" and key and value:
            async with self.config.guild(ctx.guild).variables() as variables:
                variables[key] = value
            await ctx.send(f"Variable `{key}` set to `{value}`.")
        elif action == "delete" and key:
            async with self.config.guild(ctx.guild).variables() as variables:
                if key in variables:
                    del variables[key]
                    await ctx.send(f"Variable `{key}` deleted.")
                else:
                    await ctx.send(f"Variable `{key}` not found.")
        else:
            await ctx.send("Invalid action or missing key/value. Use `view`, `set <key> <value>`, or `delete <key>`.")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        try:
            self.invites_cache[guild.id] = await guild.invites()
        except discord.Forbidden:
            print(f"Missing permissions to fetch invites for guild: {guild.name} ({guild.id})")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        if guild.id in self.invites_cache:
            del self.invites_cache[guild.id]

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        try:
            self.invites_cache[invite.guild.id] = await invite.guild.invites()
        except discord.Forbidden:
            print(f"Missing permissions to fetch invites for guild: {invite.guild.name} ({invite.guild.id})")

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        try:
            self.invites_cache[invite.guild.id] = await invite.guild.invites()
        except discord.Forbidden:
            print(f"Missing permissions to fetch invites for guild: {invite.guild.name} ({invite.guild.id})")

    async def cog_load(self):
        await self.initialize()

    async def cog_unload(self):
        self.invites_cache.clear()
