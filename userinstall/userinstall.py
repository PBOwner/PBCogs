import subprocess
import socket
import os
from redbot.core import commands, Config
from redbot.core.bot import Red

class UserInstall(commands.Cog):
    """A cog to manage user installations and count how many users have the bot installed."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567892)
        self.config.register_global(
            client_id=None,
            client_secret=None,
            redirect_uri=None,
            bot_token=None,
            venv_python_path=None,
            webserver_pid=None
        )

    @commands.group()
    @commands.is_owner()
    async def oauth(self, ctx):
        """Group of commands to configure OAuth2 credentials."""
        pass

    @oauth.command()
    async def setclientid(self, ctx, client_id: str):
        """Set the OAuth2 Client ID.

        Example:
        !oauth setclientid 123456789012345678
        """
        await self.config.client_id.set(client_id)
        confirmation = await ctx.send("OAuth2 Client ID has been set.")
        await ctx.message.delete()
        await confirmation.delete()

    @oauth.command()
    async def setclientsecret(self, ctx, client_secret: str):
        """Set the OAuth2 Client Secret.

        Example:
        !oauth setclientsecret your_client_secret_here
        """
        await self.config.client_secret.set(client_secret)
        confirmation = await ctx.send("OAuth2 Client Secret has been set.")
        await ctx.message.delete()
        await confirmation.delete()

    @oauth.command()
    async def setredirecturi(self, ctx, redirect_uri: str):
        """Set the OAuth2 Redirect URI.

        Example:
        !oauth setredirecturi https://yourdomain.com/callback
        """
        await self.config.redirect_uri.set(redirect_uri)
        confirmation = await ctx.send("OAuth2 Redirect URI has been set.")
        await ctx.message.delete()
        await confirmation.delete()

    @oauth.command()
    async def setbottoken(self, ctx, bot_token: str):
        """Set the bot token.

        Example:
        !oauth setbottoken your_bot_token_here
        """
        await self.config.bot_token.set(bot_token)
        confirmation = await ctx.send("Bot token has been set.")
        await ctx.message.delete()
        await confirmation.delete()

    @oauth.command()
    async def setvenvpythonpath(self, ctx, venv_python_path: str):
        """Set the path to the Python interpreter in the virtual environment.

        Example:
        !oauth setvenvpythonpath /path/to/your/venv/bin/python
        """
        await self.config.venv_python_path.set(venv_python_path)
        confirmation = await ctx.send("Path to the Python interpreter in the virtual environment has been set.")
        await ctx.message.delete()
        await confirmation.delete()

    @commands.command()
    async def usercount(self, ctx):
        """Get the total count of users who have installed the bot."""
        all_users = await self.config.all_users()
        installed_users = [user_id for user_id, data in all_users.items() if data['installed']]
        total_installed_users = len(installed_users)
        await ctx.send(f"The total number of users who have installed the bot is: {total_installed_users}")

    @commands.command()
    @commands.is_owner()
    async def startwebserver(self, ctx):
        """Start the Flask web server."""
        venv_python_path = await self.config.venv_python_path()
        if not venv_python_path:
            await ctx.send("The path to the Python interpreter in the virtual environment is not set. Please set it using the command `!oauth setvenvpythonpath`.")
            return

        # Get the host machine's IP address
        host_ip = socket.gethostbyname(socket.gethostname())

        await ctx.send("Starting the web server...")
        log_file = open('webserver.log', 'w')
        try:
            process = subprocess.Popen([venv_python_path, "cogs/userinstall/webserver.py", host_ip], stdout=log_file, stderr=log_file)
            await self.config.webserver_pid.set(process.pid)
            await ctx.send(f"Web server started on {host_ip} with PID {process.pid}.")
        except Exception as e:
            await ctx.send(f"Failed to start web server: {e}")

    @commands.command()
    @commands.is_owner()
    async def stopwebserver(self, ctx):
        """Stop the Flask web server."""
        webserver_pid = await self.config.webserver_pid()
        if not webserver_pid:
            await ctx.send("Web server is not running.")
            return

        try:
            subprocess.Popen(['kill', str(webserver_pid)])
            await self.config.webserver_pid.set(None)
            await ctx.send(f"Web server with PID {webserver_pid} has been stopped.")
        except Exception as e:
            await ctx.send(f"Failed to stop web server: {e}")

    @commands.command()
    @commands.is_owner()
    async def restartwebserver(self, ctx):
        """Restart the Flask web server."""
        await self.stopwebserver(ctx)
        await self.startwebserver(ctx)

def setup(bot: Red):
    bot.add_cog(UserInstall(bot))
