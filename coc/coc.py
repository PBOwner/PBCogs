import discord
from discord.ext import commands, tasks
from redbot.core import commands, Config

class COC(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "roles": []
        }
        self.config.register_guild(**default_guild)
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
    async def coc(self, ctx):
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

    @tasks.loop(minutes=3)
    async def update_chain_of_command(self):
        for guild in self.bot.guilds:
            roles = await self.config.guild(guild).roles()
            roles = sorted([guild.get_role(role_id) for role_id in roles if guild.get_role(role_id)], key=lambda r: r.position, reverse=True)

            embed = discord.Embed(title="Chain of Command", color=discord.Color.blue())
            for role in roles:
                members = [member.mention for member in role.members]
                if members:
                    embed.add_field(name=role.name, value="\n".join(members), inline=False)
                else:
                    embed.add_field(name=role.name, value="No members", inline=False)

            channel = discord.utils.get(guild.text_channels, name="chain-of-command")  # Change this to the specific channel you want to send the embed to
            if channel:
                await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.roles != after.roles:
            await self.update_chain_of_command()

def setup(bot):
    bot.add_cog(COC(bot))
