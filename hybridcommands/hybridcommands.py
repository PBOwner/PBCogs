import discord
from discord import app_commands
from discord.ext import commands
from redbot.core import commands as red_commands
from redbot.core.bot import Red

class HybridCommands(red_commands.Cog):
    """Cog for creating hybrid commands that can be used as slash commands."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.tree = bot.tree  # Use the existing CommandTree

    @red_commands.is_owner()
    @red_commands.command()
    async def register(self, ctx):
        """Register hybrid commands."""
        await self.register_commands()
        await ctx.send("Hybrid commands registered successfully!")

    async def register_commands(self):
        # Get the bot's username and use it as the command name
        command_name = self.bot.user.name.lower()

        # Define your hybrid command here
        @self.tree.command(name=command_name, description="Invoke my Wraith! >:D")
        @app_commands.describe(command="The command to run", arguments="The arguments to pass to the command")
        async def dynamic_command(interaction: discord.Interaction, command: str, arguments: str):
            await interaction.response.send_message(f"Running command: {command} with arguments: {arguments}")
            ctx = await self.bot.get_context(interaction)
            ctx.message.content = f"{ctx.prefix}{command} {arguments}"
            await self.bot.invoke(ctx)

        # Sync the command tree globally
        await self.tree.sync()

async def setup(bot: Red):
    await bot.add_cog(HybridCommands(bot))
