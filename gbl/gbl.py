import discord
from redbot.core import commands
from redbot.core import Config

class GBL(commands.Cog):
    """Cog for handling Global Ban Lists."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "nuker_raiders_list": [],
            "tos_violators_list": [],
            "case_counter": {"tos": 0}
        }
        self.config.register_guild(**default_guild)

@commands.guild_only()
@commands.command()
async def subscribe(self, ctx, list_name: str):
    """Subscribe to a ban list."""
    if list_name.lower() not in ["nuker_raiders", "tos_violators"]:
        return await ctx.send("Invalid list name. Available lists: nuker_raiders, tos_violators")

    guild = ctx.guild
    user = ctx.author

    if list_name == "nuker_raiders":
        subscribed_list = "nuker_raiders_list"
    else:
        subscribed_list = "tos_violators_list"

    async with self.config.guild(guild).get_raw(subscribed_list) as subscribed_list_data:
        if str(user.id) in subscribed_list_data:
            return await ctx.send("You are already subscribed to this list.")

        subscribed_list_data.append(str(user.id))

    await ctx.send(f"You have successfully subscribed to the {list_name} list.")
        

    @commands.guild_only()
    @commands.command()
    async def unsubscribe(self, ctx, list_name: str):
        """Unsubscribe from a ban list."""
        if list_name.lower() not in ["nuker_raiders", "tos_violators"]:
            return await ctx.send("Invalid list name. Available lists: nuker_raiders, tos_violators")

        current_list = await self.config.guild(ctx.guild).get_raw(list_name.lower() + "_list")
        if ctx.author.id in current_list:
            current_list.remove(ctx.author.id)
            await self.config.guild(ctx.guild).set_raw(list_name.lower() + "_list", value=current_list)
            await ctx.send(f"Unsubscribed from {list_name} list.")
        else:
            await ctx.send("You are not subscribed to this list.")

  @commands.guild_only()
    @commands.command()
    async def list_add(self, ctx, list_name: str, user: discord.User, reason: str, proof: str):
        """Add a user to a ban list."""
        if list_name.lower() not in ["nuker_raiders", "tos_violators"]:
            return await ctx.send("Invalid list name. Available lists: nuker_raiders, tos_violators")

        if not ctx.author.guild_permissions.administrator:
            return await ctx.send("You do not have permission to add users to the ban list.")

        case_counter = await self.config.guild(ctx.guild).case_counter()
        case_number = case_counter.get(list_name.lower(), 0) + 1

        current_list = await self.config.guild(ctx.guild).get_raw(list_name.lower() + "_list")
        case_data = {"user_id": user.id, "reason": reason, "proof": proof}

        current_list.append({"case": case_number, "data": case_data})
        await self.config.guild(ctx.guild).set_raw(list_name.lower() + "_list", value=current_list)
        case_counter[list_name.lower()] = case_number
        await self.config.guild(ctx.guild).case_counter.set(case_counter)

        await ctx.send(f"User {user.name} added to {list_name} list with case number {case_number}.")

    @commands.guild_only()
    @commands.command()
    async def list_remove(self, ctx, case_number: int, reason: str):
        """Remove a user from a ban list."""
        # Implement removing user from list logic here

    @commands.guild_only()
    @commands.command()
    async def bans_view(self, ctx, list_name: str):
        """View bans in a ban list."""
        # Implement viewing bans logic here

    @commands.guild_only()
    @commands.command()
    async def help(self, ctx):
        """Display help information."""
        # Provide help information

    @commands.guild_only()
    @commands.command()
    async def invite(self, ctx):
        """Get the invite link for the bot."""
        # Provide invite link

    @commands.guild_only()
    @commands.command()
    async def support(self, ctx):
        """Get the support server link."""
        # Provide support server link

    async def _increment_case_counter(self, guild, list_name):
        case_counter = await self.config.guild(guild).case_counter()
        case_counter[list_name] += 1
        await self.config.guild(guild).case_counter.set(case_counter)

def setup(bot):
    bot.add_cog(GBL(bot))
