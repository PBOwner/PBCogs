import discord
from redbot.core import commands, Config
from redbot.core.bot import Red

class OwnerProtection(commands.Cog):
    """A cog to protect the bot owner(s) from being muted, timed out, or banned."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_global(owners=[])

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Check if the owner is muted or timed out and reverse it."""
        owners = await self.config.owners()
        if after.id in owners:
            # Check for mute (deafened or muted)
            if before.voice and after.voice:
                if after.voice.mute or after.voice.deaf:
                    await after.edit(mute=False, deafen=False)
                    await after.send("You have been unmuted/undeafened as you are the bot owner.")
            # Check for timeout (communication_disabled_until)
            if after.timed_out_until:
                await after.edit(timed_out_until=None)
                await after.send("Your timeout has been removed as you are the bot owner.")

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        """Check if the owner is banned and reverse it."""
        owners = await self.config.owners()
        if user.id in owners:
            await guild.unban(user)
            await user.send(f"You have been unbanned from {guild.name} as you are the bot owner.")
            await guild.leave()

            # Send an embedded DM to the server owner
            owner = guild.owner
            embed = discord.Embed(title="I left", color=discord.Color.red())
            embed.add_field(name="Server", value=guild.name)
            embed.add_field(name="Reason", value=f"You banned {user.name}")
            await owner.send(embed=embed)

    @commands.group()
    @commands.is_owner()
    async def owner(self, ctx: commands.Context):
        """Group command for owner protection settings."""
        pass

    @owner.command()
    async def add(self, ctx: commands.Context, owner: discord.User):
        """Add a user to the protected owners list."""
        async with self.config.owners() as owners:
            if owner.id not in owners:
                owners.append(owner.id)
                await ctx.send(f"{owner} has been added to the protected owners list.")
            else:
                await ctx.send(f"{owner} is already in the protected owners list.")

    @owner.command()
    async def remove(self, ctx: commands.Context, owner: discord.User):
        """Remove a user from the protected owners list."""
        async with self.config.owners() as owners:
            if owner.id in owners:
                owners.remove(owner.id)
                await ctx.send(f"{owner} has been removed from the protected owners list.")
            else:
                await ctx.send(f"{owner} is not in the protected owners list.")

    @owner.command()
    async def list(self, ctx: commands.Context):
        """List all protected owners."""
        owners = await self.config.owners()
        if owners:
            owner_list = [str(self.bot.get_user(owner_id)) for owner_id in owners]
            await ctx.send(f"Protected owners: {', '.join(owner_list)}")
        else:
            await ctx.send("No protected owners.")

def setup(bot: Red):
    bot.add_cog(OwnerProtection(bot))
