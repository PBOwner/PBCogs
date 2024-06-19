import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client

class SMTPConfigModal(discord.ui.Modal):
    def __init__(self, cog: commands.Cog):
        super().__init__(title="Set SMTP Configuration")
        self.cog = cog

        self.add_item(discord.ui.InputText(label="SMTP Server", placeholder="smtp.example.com"))
        self.add_item(discord.ui.InputText(label="SMTP Port", placeholder="587"))
        self.add_item(discord.ui.InputText(label="Email Address", placeholder="example@example.com"))
        self.add_item(discord.ui.InputText(label="Email Password", placeholder="password", style=discord.InputTextStyle.password))

    async def callback(self, interaction: discord.Interaction):
        values = [item.value for item in self.children]
        keys = ["smtp_server", "smtp_port", "email_address", "email_password"]
        config_data = dict(zip(keys, values))

        for key, value in config_data.items():
            await self.cog.config.set_raw(key, value=value)

        embed = discord.Embed(
            title="SMTP Configuration Set",
            description="SMTP configuration has been set successfully.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class IMAPConfigModal(discord.ui.Modal):
    def __init__(self, cog: commands.Cog):
        super().__init__(title="Set IMAP Configuration")
        self.cog = cog

        self.add_item(discord.ui.InputText(label="IMAP Server", placeholder="imap.example.com"))
        self.add_item(discord.ui.InputText(label="IMAP Port", placeholder="993"))

    async def callback(self, interaction: discord.Interaction):
        values = [item.value for item in self.children]
        keys = ["imap_server", "imap_port"]
        config_data = dict(zip(keys, values))

        for key, value in config_data.items():
            await self.cog.config.set_raw(key, value=value)

        embed = discord.Embed(
            title="IMAP Configuration Set",
            description="IMAP configuration has been set successfully.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class TwilioConfigModal(discord.ui.Modal):
    def __init__(self, cog: commands.Cog):
        super().__init__(title="Set Twilio Configuration")
        self.cog = cog

        self.add_item(discord.ui.InputText(label="Twilio Account SID", placeholder="Your Twilio Account SID"))
        self.add_item(discord.ui.InputText(label="Twilio Auth Token", placeholder="Your Twilio Auth Token", style=discord.InputTextStyle.password))
        self.add_item(discord.ui.InputText(label="Twilio Phone Number", placeholder="+1234567890"))
        self.add_item(discord.ui.InputText(label="User Phone Number", placeholder="+1234567890"))

    async def callback(self, interaction: discord.Interaction):
        values = [item.value for item in self.children]
        keys = ["twilio_account_sid", "twilio_auth_token", "twilio_phone_number", "user_phone_number"]
        config_data = dict(zip(keys, values))

        for key, value in config_data.items():
            await self.cog.config.set_raw(key, value=value)

        embed = discord.Embed(
            title="Twilio Configuration Set",
            description="Twilio configuration has been set successfully.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class SMTPConfigButton(discord.ui.Button):
    def __init__(self, cog: commands.Cog):
        super().__init__(label="Set SMTP Configuration", style=discord.ButtonStyle.primary)
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        modal = SMTPConfigModal(self.cog)
        await interaction.response.send_modal(modal)

class IMAPConfigButton(discord.ui.Button):
    def __init__(self, cog: commands.Cog):
        super().__init__(label="Set IMAP Configuration", style=discord.ButtonStyle.primary)
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        modal = IMAPConfigModal(self.cog)
        await interaction.response.send_modal(modal)

class TwilioConfigButton(discord.ui.Button):
    def __init__(self, cog: commands.Cog):
        super().__init__(label="Set Twilio Configuration", style=discord.ButtonStyle.primary)
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        modal = TwilioConfigModal(self.cog)
        await interaction.response.send_modal(modal)

class Relay(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)  # Replace with a unique identifier
        self.config.register_global(
            smtp_server="",
            smtp_port=587,
            email_address="",
            email_password="",
            imap_server="",
            imap_port=993,
            twilio_account_sid="",
            twilio_auth_token="",
            twilio_phone_number="",
            user_phone_number=""
        )

    @commands.group()
    async def emailrelay(self, ctx):
        """Email and phone relay commands."""
        pass

    @emailrelay.command()
    async def sendemail(self, ctx, to: str, subject: str, *, body: str):
        """Send an email.

        Usage:
        [p]emailrelay sendemail recipient@example.com Subject of the email Body of the email

        Sends an email to the specified recipient with the given subject and body.
        """
        config = await self.config.all()
        msg = MIMEMultipart()
        msg['From'] = config['email_address']
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        try:
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
            server.starttls()
            server.login(config['email_address'], config['email_password'])
            text = msg.as_string()
            server.sendmail(config['email_address'], to, text)
            server.quit()
            embed = discord.Embed(
                title="Email Sent",
                description="Email sent successfully.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"Failed to send email: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @emailrelay.command()
    async def checkemail(self, ctx):
        """Check for new emails.

        Usage:
        [p]emailrelay checkemail

        Checks for new unread emails in the inbox and displays them.
        """
        config = await self.config.all()
        try:
            mail = imaplib.IMAP4_SSL(config['imap_server'], config['imap_port'])
            mail.login(config['email_address'], config['email_password'])
            mail.select('inbox')

            status, messages = mail.search(None, 'UNSEEN')
            email_ids = messages[0].split()

            if not email_ids:
                embed = discord.Embed(
                    title="No New Emails",
                    description="There are no new emails.",
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)
                return

            for email_id in email_ids:
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                msg = email.message_from_bytes(msg_data[0][1])
                subject = msg['subject']
                from_ = msg['from']
                body = ""

                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode()
                            break
                else:
                    body = msg.get_payload(decode=True).decode()

                embed = discord.Embed(
                    title="New Email",
                    description=f"From: {from_}\nSubject: {subject}\n\n{body}",
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)

            mail.logout()
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"Failed to check emails: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command()
    async def relaycall(self, ctx, to: str, message: str):
        """Relay a call from Discord to a phone number.

        Usage:
        [p]relaycall +1234567890 Your message here

        Relays a call from Discord to the specified phone number with the given message.

        To get your Twilio Account SID, Auth Token, and Phone Number:
        1. Sign up for a Twilio account at https://www.twilio.com/.
        2. Go to your Twilio Console Dashboard.
        3. Find your Account SID and Auth Token.
        4. Purchase a Twilio phone number.
        """
        config = await self.config.all()
        try:
            client = Client(config['twilio_account_sid'], config['twilio_auth_token'])
            call = client.calls.create(
                twiml=f'<Response><Say>{message}</Say></Response>',
                to=to,
                from_=config['twilio_phone_number']
            )
            embed = discord.Embed(
                title="Call Initiated",
                description=f"Call initiated successfully. Call SID: {call.sid}",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"Failed to initiate call: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @emailrelay.command()
    async def setconfig(self, ctx):
        """Set configuration values.

        Usage:
        [p]emailrelay setconfig

        Opens a modal to set the configuration values for email and Twilio settings.
        """
        view = discord.ui.View()
        view.add_item(SMTPConfigButton(self))
        view.add_item(IMAPConfigButton(self))
        view.add_item(TwilioConfigButton(self))
        embed = discord.Embed(
            title="Set Configuration",
            description="Click the buttons below to set the configuration values.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed, view=view)

def setup(bot: Red):
    bot.add_cog(Relay(bot))
