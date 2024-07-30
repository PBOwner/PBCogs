from redbot.core import commands, Config
from discord.http import Route
import discord

class SlashRouter(commands.Cog):
    """Cog to route text commands to slash commands for user installation."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_global = {
            "commands": {}
        }
        self.config.register_global(**default_global)

    @commands.command()
    async def futurobot(self, ctx):
        """A command to route text commands to slash commands."""
        command = self.bot.tree.get_command("futurobot")
        if command is None:
            await ctx.send("Slash command 'futurobot' not found.")
            return

        payload = command.to_dict()
        payload.update(integration_types=[0, 1], contexts=[0, 1, 2])

        r = Route(
            'POST',
            '/applications/{application_id}/commands',
            application_id=self.bot.application_id,
        )

        try:
            await self.bot.http.request(r, json=payload)
            await ctx.send("Slash command 'futurobot' has been routed successfully.")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to route command: {e}")

def setup(bot):
    bot.add_cog(SlashRouter(bot))
