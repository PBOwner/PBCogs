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
        with open(f'{self.template_dir}/{template_id}.json', 'w') as f:
            json.dump(template.__dict__, f)

        await ctx.send(f'Template saved with ID: {template_id}')

    @commands.command()
    async def loadt(self, ctx, template_id: str):
        """Loads a template and applies it to the current server."""
        guild = ctx.guild

        # Load template
        try:
            with open(f'{self.template_dir}/{template_id}.json', 'r') as f:
                template_data = json.load(f)
        except FileNotFoundError:
            await ctx.send('Template not found.')
            return

        template = ServerTemplate(**template_data)

        # Clear existing channels and roles
        for channel in guild.channels:
            await channel.delete()
        for role in guild.roles:
            if role != guild.default_role:
                await role.delete()

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
            for role_name, perm in channel_data['permissions'].items():
                overwrites[role_map[role_name]] = discord.PermissionOverwrite(
                    read_messages=perm['read_messages'],
                    send_messages=perm['send_messages']
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

def setup(bot):
    bot.add_cog(Xenon(bot))
