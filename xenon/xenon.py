import discord
from redbot.core import commands
import json
import os
import uuid

class ServerTemplate:
    def __init__(self, channels, roles):
        self.channels = channels
        self.roles = roles

class Xenon(commands.Cog):
    """A cog that copies servers as templates and applies them to other servers."""

    def __init__(self, bot):
        self.bot = bot
        self.template_dir = 'templates'
        # Ensure the templates directory exists
        if not os.path.exists(self.template_dir):
            os.makedirs(self.template_dir)

    @commands.command()
    async def savet(self, ctx):
        """Saves the current server's structure as a template."""
        guild = ctx.guild
        channels = []
        roles = []

        # Save channels
        for channel in guild.channels:
            permissions = {}
            for role, perm in channel.overwrites.items():
                permissions[str(role.id)] = {
                    'read_messages': perm.pair()[0],
                    'send_messages': perm.pair()[1]
                }
            channels.append({
                'name': channel.name,
                'type': str(channel.type),
                'position': channel.position,
                'permissions': permissions
            })

        # Save roles
        for role in guild.roles:
            roles.append({
                'name': role.name,
                'permissions': role.permissions.value,  # Convert permissions to integer
                'position': role.position,
                'color': role.color.value,
                'hoist': role.hoist,
                'mentionable': role.mentionable
            })

        template = ServerTemplate(channels, roles)
        template_id = str(uuid.uuid4())
        
        # Use custom JSON encoder
        with open(f'{self.template_dir}/{template_id}.json', 'w') as f:
            json.dump(template.__dict__, f, cls=CustomJSONEncoder)

        await ctx.send(f'Template saved with ID: {template_id}')

    @commands.command()
    async def loadt(self, ctx, template_id: str):
        """Loads a template and applies it to the current server.

        This command will delete all existing channels and roles on the server
        and recreate them based on the specified template.

        Parameters
        ----------
        template_id : str
            The ID of the template to load.
        """
        guild = ctx.guild

        # Check if the user has the required permissions
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.send("You need the 'Manage Server' permission to use this command.")
            return

        # Load template
        try:
            with open(f'{self.template_dir}/{template_id}.json', 'r') as f:
                template_data = json.load(f)
        except FileNotFoundError:
            await ctx.send('Template not found.')
            return

        # Disable community features if enabled
        if 'COMMUNITY' in guild.features:
            try:
                # **Fix:** Set verification level to None first, then disable explicit content filter
                await guild.edit(verification_level=discord.VerificationLevel.none)
                await guild.edit(explicit_content_filter=discord.ContentFilter.disabled)
                await guild.edit(default_notifications=discord.NotificationLevel.all_messages)
            except discord.HTTPException as e:
                await ctx.send(f"Failed to disable community features: {str(e)}")
                return

        # Clear existing channels and roles
        for channel in list(guild.channels):
            try:
                await channel.delete()
            except discord.HTTPException as e:
                await ctx.send(f"Failed to delete channel {channel.name}: {str(e)}")

        for role in list(guild.roles):
            if role != guild.default_role and not role.managed:
                try:
                    await role.delete()
                except discord.HTTPException as e:
                    await ctx.send(f"Failed to delete role {role.name}: {str(e)}")

        template = ServerTemplate(**template_data)

        # Create roles
        role_map = {}
        for role_data in template.roles:
            role = await guild.create_role(
                name=role_data['name'],
                permissions=discord.Permissions(role_data['permissions']),  # Convert integer to Permissions
                color=discord.Color(role_data['color']),
                hoist=role_data['hoist'],
                mentionable=role_data['mentionable']
            )
            role_map[role_data['name']] = role

        # Create channels
        for channel_data in template.channels:
            overwrites = {}
            for role_id, perm in channel_data['permissions'].items():
                role = role_map.get(role_id)
                if role:
                    overwrites[role] = discord.PermissionOverwrite.from_pair(
                        discord.Permissions(perm['allow']),
                        discord.Permissions(perm['deny'])
                    )
            if channel_data['type'] == 'text':
                await guild.create_text_channel(
                    name=channel_data['name'],
                    position=channel_data['position'],
                    overwrites=overwrites
                )
            elif channel_data['type'] == 'voice':
                await guild.create_voice_channel(
                    name=channel_data['name'],
                    position=channel_data['position'],
                    overwrites=overwrites
                )

        # Re-enable community features if they were originally enabled
        if 'COMMUNITY' in guild.features:
            try:
                # **Fix:** Set verification level to low first, then set explicit content filter
                await guild.edit(verification_level=discord.VerificationLevel.low)
                await guild.edit(explicit_content_filter=discord.ContentFilter.no_role)
                await guild.edit(default_notifications=discord.NotificationLevel.only_mentions)
            except discord.HTTPException as e:
                await ctx.send(f"Failed to re-enable community features: {str(e)}")
                return

        await ctx.send('Template applied successfully.')
    @commands.command()
    async def listt(self, ctx):
        """Lists all saved templates."""
        template_files = os.listdir(self.template_dir)
        if not template_files:
            await ctx.send('No templates found.')
            return

        embed = discord.Embed(title="Saved Templates", color=discord.Color.blue())
        for template_file in template_files:
            template_id = template_file.split('.')[0]
            embed.add_field(name=template_id, value=f"Template ID: {template_id}", inline=False)

        await ctx.send(embed=embed)

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON Encoder to handle discord.Permissions objects."""
    def default(self, obj):
        if isinstance(obj, discord.Permissions):
            return obj.value
        return super().default(obj)

def setup(bot):
    bot.add_cog(Xenon(bot))
