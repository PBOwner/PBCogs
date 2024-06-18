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
        
# Custom JSON Encoder might be needed to handle complex objects
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, discord.Permissions):
            return obj.value
        return json.JSONEncoder.default(self, obj)

# Helper function to check if a user is the owner or a trusted user
def is_owner_or_trusted(ctx):
    return ctx.author.id in ctx.cog.trusted_users or ctx.bot.is_owner(ctx.author)

class ServerTemplate:
    def __init__(self, verification_level, explicit_content_filter, default_notifications, roles, channels):
        """
        Initialize a ServerTemplate instance.

        :param verification_level: The verification level of the server.
        :param explicit_content_filter: The explicit content filter level of the server.
        :param default_notifications: The default notification settings of the server.
        :param roles: A list of roles in the server.
        :param channels: A list of channels in the server.
        """
        self.verification_level = verification_level
        self.explicit_content_filter = explicit_content_filter
        self.default_notifications = default_notifications
        self.roles = roles
        self.channels = channels

class Xenon(commands.Cog):
    """Cog for saving and loading server templates."""
    
    def __init__(self, bot):
        self.bot = bot
        self.template_dir = 'templates'
        # Ensure the templates directory exists
        if not os.path.exists(self.template_dir):
            os.makedirs(self.template_dir)
        self.trusted_users = set()  # This should be populated appropriately

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
        verification_level = guild.verification_level.value  # Save verification level as integer
        explicit_content_filter = guild.explicit_content_filter.value  # Save explicit content filter as integer
        default_notifications = guild.default_notifications.value  # Save default notifications as integer

        # Create the ServerTemplate instance with the correct order of parameters
        template = ServerTemplate(
            verification_level=verification_level,
            explicit_content_filter=explicit_content_filter,
            default_notifications=default_notifications,
            roles=roles,
            channels=channels
        )
        
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

        # Debugging statement to check the type of verification_level
        print(f"Loaded verification_level: {template.verification_level} (type: {type(template.verification_level)})")

        # Validate template data
        if not isinstance(template.verification_level, int):
            await ctx.send('Invalid template: verification_level must be a integer.')
            return

        # Disable community features if enabled
        if 'COMMUNITY' in guild.features:
            try:
                # Convert verification level string to enum value
                verification_level = discord.VerificationLevel(template.verification_level)
                await guild.edit(verification_level=verification_level)

                # Set explicit content filter to the same as the template
                await guild.edit(explicit_content_filter=discord.ContentFilter(template.explicit_content_filter))

                # Set default notifications to the same as the template
                await guild.edit(default_notifications=discord.NotificationLevel(template.default_notifications))
            except discord.HTTPException as e:
                await ctx.send(f"Failed to disable community features: {str(e)}")
                return
            except KeyError:
                await ctx.send(f"Invalid verification level in template: {template.verification_level}")
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
                await guild.edit(explicit_content_filter=discord.ContentFilter(template.explicit_content_filter))
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
