import discord
from discord.ext import commands, tasks
from redbot.core import commands, Config

class COC(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "roles": [],
            "channel_id": None
        }
        self.config.register_guild(**default_guild)
        self.previous_roles = {}
        self.update_chain_of_command.start()

    def cog_unload(self):
        self.update_chain_of_command.cancel()

    @commands.command()
    async def addrank(self, ctx, role: discord.Role):
        async with self.config.guild(ctx.guild).roles() as roles:
            if role.id not in roles:
                roles.append(role.id)
                await ctx.send(embed=discord.Embed(title="Role Added", description=f"Role `{role.name}` has been added to the list.", color=discord.Color.green()))
            else:
                await ctx.send(embed=discord.Embed(title="Role Exists", description=f"Role `{role.name}` is already in the list.", color=discord.Color.yellow()))

    @commands.command()
    async def remrank(self, ctx, role: discord.Role):
        async with self.config.guild(ctx.guild).roles() as roles:
            if role.id in roles:
                roles.remove(role.id)
                await ctx.send(embed=discord.Embed(title="Role Removed", description=f"Role `{role.name}` has been removed from the list.", color=discord.Color.red()))
            else:
                await ctx.send(embed=discord.Embed(title="Role Not Found", description=f"Role `{role.name}` is not in the list.", color=discord.Color.yellow()))

    @commands.group(invoke_without_command=True)
    async def coc(self, ctx):
        """Show a preview of the Chain of Command."""
        guild = ctx.guild
        roles = await self.config.guild(guild).roles()
        roles = sorted([guild.get_role(role_id) for role_id in roles if guild.get_role(role_id)], key=lambda r: r.position, reverse=True)

        embed = discord.Embed(title="Chain of Command", color=discord.Color.blue())
        for role in roles:
            members = [member.mention for member in role.members]
            if members:
                embed.add_field(name=role.name, value="\n".join(members), inline=False)
            else:
                embed.add_field(name=role.name, value="No members", inline=False)

        await ctx.send(embed=embed)

    @coc.command()
    async def channel(self, ctx, channel: discord.TextChannel):
        """Set the channel for the dynamically updating embed."""
        await self.config.guild(ctx.guild).channel_id.set(channel.id)
        await ctx.send(embed=discord.Embed(title="Channel Set", description=f"The channel `{channel.name}` has been set for the Chain of Command updates.", color=discord.Color.green()))

    @coc.command()
    async def send(self, ctx):
        """Send the Chain of Command embed to the set channel."""
        guild = ctx.guild
        channel_id = await self.config.guild(guild).channel_id()
        if channel_id is None:
            await ctx.send(embed=discord.Embed(title="Channel Not Set", description="Please set a channel using the `coc channel` command first.", color=discord.Color.red()))
            return

        channel = guild.get_channel(channel_id)
        if channel is None:
            await ctx.send(embed=discord.Embed(title="Channel Not Found", description="The set channel could not be found. Please set a valid channel using the `coc channel` command.", color=discord.Color.red()))
            return

        roles = await self.config.guild(guild).roles()
        roles = sorted([guild.get_role(role_id) for role_id in roles if guild.get_role(role_id)], key=lambda r: r.position, reverse=True)

        embed = discord.Embed(title="Chain of Command", color=discord.Color.blue())
        for role in roles:
            members = [member.mention for member in role.members]
            if members:
                embed.add_field(name=role.name, value="\n".join(members), inline=False)
            else:
                embed.add_field(name=role.name, value="No members", inline=False)

        await channel.send(embed=embed)

    @coc.command()
    async def update(self, ctx):
        """Manually update the Chain of Command embed."""
        guild = ctx.guild
        channel_id = await self.config.guild(guild).channel_id()
        if channel_id is None:
            await ctx.send(embed=discord.Embed(title="Channel Not Set", description="Please set a channel using the `coc channel` command first.", color=discord.Color.red()))
            return

        channel = guild.get_channel(channel_id)
        if channel is None:
            await ctx.send(embed=discord.Embed(title="Channel Not Found", description="The set channel could not be found. Please set a valid channel using the `coc channel` command.", color=discord.Color.red()))
            return

        roles = await self.config.guild(guild).roles()
        roles = sorted([guild.get_role(role_id) for role_id in roles if guild.get_role(role_id)], key=lambda r: r.position, reverse=True)

        embed = discord.Embed(title="Chain of Command", color=discord.Color.blue())
        for role in roles:
            members = [member.mention for member in role.members]
            if members:
                embed.add_field(name=role.name, value="\n".join(members), inline=False)
            else:
                embed.add_field(name=role.name, value="No members", inline=False)

        await channel.send(embed=embed)
        await ctx.send(embed=discord.Embed(title="Chain of Command Updated", description="The Chain of Command embed has been manually updated.", color=discord.Color.green()))

    @tasks.loop(minutes=2)
    async def update_chain_of_command(self):
        for guild in self.bot.guilds:
            roles = await self.config.guild(guild).roles()
            roles = sorted([guild.get_role(role_id) for role_id in roles if guild.get_role(role_id)], key=lambda r: r.position, reverse=True)

            updated = False
            current_roles = {}
            for role in roles:
                current_roles[role.id] = {member.id for member in role.members}

            if guild.id not in self.previous_roles:
                self.previous_roles[guild.id] = {}

            for role_id, members in current_roles.items():
                if role_id not in self.previous_roles[guild.id] or self.previous_roles[guild.id][role_id] != members:
                    updated = True
                    break

            if updated:
                embed = discord.Embed(title="Chain of Command", color=discord.Color.blue())
                for role in roles:
                    members = [member.mention for member in role.members]
                    if members:
                        embed.add_field(name=role.name, value="\n".join(members), inline=False)
                    else:
                        embed.add_field(name=role.name, value="No members", inline=False)

                channel_id = await self.config.guild(guild).channel_id()
                if channel_id:
                    channel = guild.get_channel(channel_id)
                    if channel:
                        await channel.send(embed=embed)

                self.previous_roles[guild.id] = current_roles

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.roles != after.roles:
            await self.update_chain_of_command()

    @commands.is_owner()
    @commands.command()
    async def resetguild(self, ctx):
        """Reset the current guild's configuration."""
        await self.config.clear_all_guilds()
        await ctx.send(embed=discord.Embed(title="Reset Guild Configuration", description=f"The configuration for guild `{ctx.guild.name}` has been reset.", color=discord.Color.red()))

    @commands.is_owner()
    @commands.command()
    async def resetallguilds(self, ctx):
        """Reset all guilds' configurations."""
        await self.config.clear_all()
        await ctx.send(embed=discord.Embed(title="Reset All Guilds' Configurations", description="The configurations for all guilds have been reset.", color=discord.Color.red()))
