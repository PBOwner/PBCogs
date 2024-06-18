import discord
from redbot.core import commands
import json
import os
import uuid

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle discord.Permissions objects."""
    def default(self, obj):
        if isinstance(obj, discord.Permissions):
            return obj.value
        return super().default(obj)

class ServerTemplate:
    """Represents a server template."""
    def __init__(self, bot):
        """Initializes the ServerTemplate class."""
        self.bot = bot
        self.template_dir = 'templates'
        # Ensure the templates directory exists
        if not os.path.exists(self.template_dir):
            os.makedirs(self.template_dir)
        self.trusted_users = set()

    def save_template(self, guild, template_id):
        """Saves the current server's structure as a template."""
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

        # Save additional guild settings
        verification_level = guild.verification_level
        explicit_content_filter = guild.explicit_content_filter
        default_notifications = guild.default_notifications

        template_data = {
            'channels': channels,
            'roles': roles,
            'verification_level': verification_level,
            'explicit_content_filter': explicit_content_filter,
            'default_notifications': default_notifications
        }

        # Use custom JSON encoder
        with open(f'{self.template_dir}/{template_id}.json', 'w') as f:
            json.dump(template_data, f, cls=CustomJSONEncoder)

class ServerTemplates(commands.Cog):
    """Cog for saving and loading server templates."""
    def __init__(self, bot):
        self.bot = bot
        self.server_template = ServerTemplate(bot)

    def is_owner_or_trusted(ctx):
        return ctx.author == ctx.guild.owner or ctx.author.id in ctx.cog.trusted_users

    @commands.command()
    @commands.check(is_owner_or_trusted)
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

        # Save additional guild settings
        verification_level = guild.verification_level
        explicit_content_filter = guild.explicit_content_filter
        default_notifications = guild.default_notifications

        template = ServerTemplate(channels, roles, verification_level, explicit_content_filter, default_notifications)
        template_id = str(uuid.uuid4())
        
        # Use custom JSON encoder
        with open(f'{self.template_dir}/{template_id}.json', 'w') as f:
            json.dump(template.__dict__, f, cls=CustomJSONEncoder)

        await ctx.send(f'Template saved with ID: {template_id}')

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def addtrusted(self, ctx, user: commands.MemberConverter):
        """Adds a trusted user who can run the savet and loadt commands."""
        self.trusted_users.add(user.id)
        await ctx.send(f'{user.mention} has been added as a trusted user.')

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def remtrusted(self, ctx, user: commands.MemberConverter):
        """Removes a trusted user."""
        self.trusted_users.discard(user.id)
        await ctx.send(f'{user.mention} has been removed from trusted users.')

    @commands.command()
    @commands.check(is_owner_or_trusted)
    async def loadt(self, ctx, template_id):
        """Loads a template and applies it to the current server.

        This command will delete all existing channels and roles on the server
        and recreate them based on the specified template.

        Parameters
        ----------
        template_id : str
            The ID of the template to load.
        """
        guild = ctx.guild

        # Load template
        try:
            with open(f'{self.template_dir}/{template_id}.json', 'r') as f:
                template_data = json.load(f)
        except FileNotFoundError:
            await ctx.send('Template not found.')
            return

        template = ServerTemplate(**template_data)

        # Disable community features if enabled
        if 'COMMUNITY' in guild.features:
            try:
                # Set verification level to the same as the template
                await guild.edit(verification_level=discord.VerificationLevel(template.verification_level))
                # Set explicit content filter to the same as the template
                await guild.edit(explicit_content_filter=discord.ContentFilter(template.explicit_content_filter))
                # Set default notifications to the same as the template
                await guild.edit(default_notifications=discord.NotificationLevel(template.default_notifications))
            except discord.HTTPException as e:
                await ctx.send(f"Failed to disable community features: {str(e)}")
                return

        # Clear existing channels and roles
        for channel in list(guild.channels):
            try:
                await channel.delete()  # Move the 'await' statement inside the function
            except discord.HTTPException as e:
                await ctx.send(f"Failed to delete channel {channel.name}: {str(e)}")

        for role in list(guild.roles):
            if role != guild.default_role and not role.managed:
                try:
                    await role.delete()
                except discord.HTTPException as e:
                    await ctx.send(f"Failed to delete role {role.name}: {str(e)}")

        # Create roles
        role_map = {}
        for role_data in template.roles:
            role = await guild.create_role(
                name=role_data['name'],
                permissions=discord.Permissions(role_data['permissions']),
                color=discord.Color(role_data['color']),
                hoist=role_data['hoist'],
                mentionable=role_data['mentionable']
            )
            role_map[role_data['name']] = role

        # Create channels
        for channel_data in template.channels:
            overwrites = {}
            for role_id, perm in channel_data['permissions'].items():
                role = discord.utils.get(guild.roles, id=int(role_id))
                if role:
                    overwrites[role] = discord.PermissionOverwrite(
                        read_messages=perm['read_messages'],
                        send_messages=perm['send_messages']
                    )
            await guild.create_text_channel(
                name=channel_data['name'],
                overwrites=overwrites,
                position=channel_data['position']
            )
            
        # Re-enable community features if they were originally enabled
        if 'COMMUNITY' in guild.features:
            try:
                # Set verification level to the same as the template
                await guild.edit(verification_level=discord.VerificationLevel(template.verification_level))
                # Set explicit content filter to the same as the template
                await guild.edit(explicit_content_filter=discord.ContentFilter(template.explicit_content_filter))
                # Set default notifications to the same as the template
                await guild.edit(default_notifications=discord.NotificationLevel(template.default_notifications))
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
