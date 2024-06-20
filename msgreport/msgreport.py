import discord
from redbot.core import commands, Config, checks

class MsgReport(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "report_channel": None
        }
        self.config.register_guild(**default_guild)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def setreportchannel(self, ctx, channel: discord.TextChannel):
        """Set the channel where reports will be sent."""
        await self.config.guild(ctx.guild).report_channel.set(channel.id)
        await ctx.send(f"Report channel set to {channel.mention}")

    @commands.command()
    async def reportmsg(self, ctx, message_link: str, *, reason: str):
        """Report a message with a reason."""
        report_channel_id = await self.config.guild(ctx.guild).report_channel()
        if not report_channel_id:
            return await ctx.send("The report channel has not been set.")

        report_channel = ctx.guild.get_channel(report_channel_id)
        if not report_channel:
            return await ctx.send("The report channel is invalid.")

        try:
            message_info = await self._get_message_from_link(ctx, message_link)
            if not message_info:
                return await ctx.send("Invalid message link.")
        except Exception as e:
            return await ctx.send(f"Error retrieving message: {e}")

        embed = discord.Embed(title="Message Reported", color=discord.Color.red())
        embed.add_field(name="Who Reported", value=ctx.author.mention, inline=False)
        embed.add_field(name="What was reported", value=message_link, inline=False)
        embed.add_field(name="Why it was reported", value=reason, inline=False)
        embed.add_field(name="Message Content", value=message_info.content, inline=False)
        embed.set_footer(text="React with ✅ to accept or ❌ to deny")

        report_message = await report_channel.send(embed=embed)
        await report_message.add_reaction("✅")
        await report_message.add_reaction("❌")

    async def _get_message_from_link(self, ctx, message_link: str):
        parts = message_link.split('/')
        if len(parts) < 3:
            return None

        guild_id = int(parts[-3])
        channel_id = int(parts[-2])
        message_id = int(parts[-1])

        if guild_id != ctx.guild.id:
            return None

        channel = ctx.guild.get_channel(channel_id)
        if not channel:
            return None

        message = await channel.fetch_message(message_id)
        return message

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id:
            return

        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)

        if not member.guild_permissions.manage_messages:
            return

        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        reaction = discord.utils.get(message.reactions, emoji=payload.emoji.name)

        if reaction and reaction.count > 1:
            embed = message.embeds[0]
            if payload.emoji.name == "✅":
                message_link_field = next((field for field in embed.fields if field.name == "What was reported"), None)
                if message_link_field:
                    message_link = message_link_field.value
                    message_info = await self._get_message_from_link(member, message_link)
                    if message_info:
                        await message_info.delete()
                        await message.channel.send(f"Message deleted by {member.mention}")
            elif payload.emoji.name == "❌":
                await message.channel.send(f"Report denied by {member.mention}")

def setup(bot):
    bot.add_cog(MsgReport(bot))
