import discord
from discord.ext import commands, tasks
from redbot.core import Config, checks
from redbot.core.bot import Red
from datetime import datetime

class VoiceChannelManager(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)  # Replace with a unique identifier
        default_guild = {
            "designated_voice_channel": None,
            "voice_channels": {}
        }
        self.config.register_guild(**default_guild)
        self.voice_channel_check.start()

    @commands.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def setchannel(self, ctx, channel: discord.VoiceChannel):
        """Set the designated voice channel for creating private voice channels."""
        await self.config.guild(ctx.guild).designated_voice_channel.set(channel.id)
        embed = discord.Embed(
            title="Designated Channel Set",
            description=f"The designated voice channel has been set to {channel.mention}.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @tasks.loop(seconds=10)
    async def voice_channel_check(self):
        for guild in self.bot.guilds:
            designated_channel_id = await self.config.guild(guild).designated_voice_channel()
            if designated_channel_id:
                designated_channel = guild.get_channel(designated_channel_id)
                if designated_channel and len(designated_channel.members) > 0:
                    for member in designated_channel.members:
                        await self.create_private_voice_channel(member, designated_channel)

    async def create_private_voice_channel(self, member: discord.Member, designated_channel: discord.VoiceChannel):
        overwrites = {
            member.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, connect=True, manage_channels=True)
        }
        category = discord.utils.get(member.guild.categories, name="Voice Channels")  # You can change the category name
        if not category:
            category = await member.guild.create_category("Voice Channels")

        voice_channel = await member.guild.create_voice_channel(f"{member.name}'s Channel", overwrites=overwrites, category=category)

        creation_time = datetime.utcnow().isoformat()
        await self.config.guild(member.guild).voice_channels.set_raw(
            str(voice_channel.id),
            value={
                "name": f"{member.name}'s Channel",
                "creator": member.id,
                "creation_time": creation_time,
                "member_limit": None,
                "hidden": False
            }
        )

        await member.move_to(voice_channel)
        view = VoiceChannelControlView(self, voice_channel.id)
        embed = discord.Embed(
            title="Voice Channel Created",
            description=f"Voice channel '{voice_channel.name}' has been created for {member.mention}.",
            color=discord.Color.green()
        )
        await voice_channel.send(embed=embed, view=view)

class VoiceChannelControlView(discord.ui.View):
    def __init__(self, cog: commands.Cog, channel_id: int):
        super().__init__(timeout=None)
        self.cog = cog
        self.channel_id = channel_id

    @discord.ui.button(label="Lock Channel", style=discord.ButtonStyle.red)
    async def lock_channel(self, button: discord.ui.Button, interaction: discord.Interaction):
        channel = interaction.guild.get_channel(self.channel_id)
        if channel:
            await channel.set_permissions(interaction.guild.default_role, connect=False)
            await interaction.response.send_message("Channel locked.", ephemeral=True)

    @discord.ui.button(label="Unlock Channel", style=discord.ButtonStyle.green)
    async def unlock_channel(self, button: discord.ui.Button, interaction: discord.Interaction):
        channel = interaction.guild.get_channel(self.channel_id)
        if channel:
            await channel.set_permissions(interaction.guild.default_role, connect=True)
            await interaction.response.send_message("Channel unlocked.", ephemeral=True)

    @discord.ui.button(label="Hide Channel", style=discord.ButtonStyle.red)
    async def hide_channel(self, button: discord.ui.Button, interaction: discord.Interaction):
        channel = interaction.guild.get_channel(self.channel_id)
        if channel:
            await channel.set_permissions(interaction.guild.default_role, view_channel=False)
            await self.cog.config.guild(channel.guild).voice_channels.set_raw(str(channel.id), value={"hidden": True})
            await interaction.response.send_message("Channel hidden.", ephemeral=True)

    @discord.ui.button(label="Reveal Channel", style=discord.ButtonStyle.green)
    async def reveal_channel(self, button: discord.ui.Button, interaction: discord.Interaction):
        channel = interaction.guild.get_channel(self.channel_id)
        if channel:
            await channel.set_permissions(interaction.guild.default_role, view_channel=True)
            await self.cog.config.guild(channel.guild).voice_channels.set_raw(str(channel.id), value={"hidden": False})
            await interaction.response.send_message("Channel revealed.", ephemeral=True)

    @discord.ui.button(label="Rename Channel", style=discord.ButtonStyle.blurple)
    async def rename_channel(self, button: discord.ui.Button, interaction: discord.Interaction):
        modal = RenameChannelModal(self.cog, self.channel_id)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Increase Limit", style=discord.ButtonStyle.blurple)
    async def increase_limit(self, button: discord.ui.Button, interaction: discord.Interaction):
        channel = interaction.guild.get_channel(self.channel_id)
        if channel:
            new_limit = channel.user_limit + 1 if channel.user_limit else 1
            await channel.edit(user_limit=new_limit)
            await self.cog.config.guild(channel.guild).voice_channels.set_raw(str(channel.id), value={"member_limit": new_limit})
            await interaction.response.send_message(f"Member limit increased to {new_limit}.", ephemeral=True)

    @discord.ui.button(label="Decrease Limit", style=discord.ButtonStyle.blurple)
    async def decrease_limit(self, button: discord.ui.Button, interaction: discord.Interaction):
        channel = interaction.guild.get_channel(self.channel_id)
        if channel and channel.user_limit and channel.user_limit > 1:
            new_limit = channel.user_limit - 1
            await channel.edit(user_limit=new_limit)
            await self.cog.config.guild(channel.guild).voice_channels.set_raw(str(channel.id), value={"member_limit": new_limit})
            await interaction.response.send_message(f"Member limit decreased to {new_limit}.", ephemeral=True)

    @discord.ui.button(label="Channel Info", style=discord.ButtonStyle.gray)
    async def channel_info(self, button: discord.ui.Button, interaction: discord.Interaction):
        channel = interaction.guild.get_channel(self.channel_id)
        if channel:
            config = await self.cog.config.guild(channel.guild).voice_channels.get_raw(str(channel.id))
            creator = interaction.guild.get_member(config["creator"])
            creation_time = datetime.fromisoformat(config["creation_time"])
            hidden = config["hidden"]
            member_limit = config["member_limit"]

            embed = discord.Embed(
                title="Voice Channel Info",
                description=f"**Name:** {channel.name}\n**Creator:** {creator.mention}\n**Created At:** {creation_time}\n**Hidden:** {hidden}\n**Member Limit:** {member_limit}",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Kick Member", style=discord.ButtonStyle.red)
    async def kick_member(self, button: discord.ui.Button, interaction: discord.Interaction):
        modal = KickMemberModal(self.cog, self.channel_id)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Claim Channel", style=discord.ButtonStyle.green)
    async def claim_channel(self, button: discord.ui.Button, interaction: discord.Interaction):
        channel = interaction.guild.get_channel(self.channel_id)
        if channel:
            config = await self.cog.config.guild(channel.guild).voice_channels.get_raw(str(channel.id))
            creator = interaction.guild.get_member(config["creator"])
            if creator == interaction.user:
                await interaction.response.send_message("You are already the creator of this channel.", ephemeral=True)
            else:
                await self.cog.config.guild(channel.guild).voice_channels.set_raw(str(channel.id), value={"creator": interaction.user.id})
                await channel.set_permissions(interaction.user, connect=True, manage_channels=True)
                await interaction.response.send_message("You have claimed the channel.", ephemeral=True)

class RenameChannelModal(discord.ui.Modal):
    def __init__(self, cog: commands.Cog, channel_id: int):
        super().__init__(title="Rename Channel")
        self.cog = cog
        self.channel_id = channel_id
        self.add_item(discord.ui.InputText(label="New Channel Name", placeholder="Enter new channel name"))

    async def callback(self, interaction: discord.Interaction):
        new_name = self.children[0].value
        channel = interaction.guild.get_channel(self.channel_id)
        if channel:
            await channel.edit(name=new_name)
            await self.cog.config.guild(channel.guild).voice_channels.set_raw(str(channel.id), value={"name": new_name})
            await interaction.response.send_message(f"Channel renamed to {new_name}.", ephemeral=True)

class KickMemberModal(discord.ui.Modal):
    def __init__(self, cog: commands.Cog, channel_id: int):
        super().__init__(title="Kick Member")
        self.cog = cog
        self.channel_id = channel_id
        self.add_item(discord.ui.InputText(label="Member ID", placeholder="Enter member ID to kick"))

    async def callback(self, interaction: discord.Interaction):
        member_id = int(self.children[0].value)
        member = interaction.guild.get_member(member_id)
        channel = interaction.guild.get_channel(self.channel_id)
        if member and channel:
            await member.move_to(None)
            await interaction.response.send_message(f"{member.mention} has been kicked from the channel.", ephemeral=True)

def setup(bot: Red):
    bot.add_cog(VoiceChannelManager(bot))
