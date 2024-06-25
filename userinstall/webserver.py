import os
import sys
import asyncio
from flask import Flask, redirect, request, session
import requests
from redbot.core import Config
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, filename='webserver.log', filemode='a', format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
app.secret_key = os.urandom(24)

config = Config.get_conf(None, identifier=1234567892)
config.register_user(installed=False)

@app.route('/')
def home():
    return 'Hello, this is the home page.'

@app.route('/login')
def login():
    client_id = asyncio.run(config.client_id())
    redirect_uri = asyncio.run(config.redirect_uri())
    scope = 'identify'
    discord_login_url = f'https://discord.com/api/oauth2/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scope}'
    return redirect(discord_login_url)

@app.route('/callback')
def callback():
    client_id = asyncio.run(config.client_id())
    client_secret = asyncio.run(config.client_secret())
    redirect_uri = asyncio.run(config.redirect_uri())
    code = request.args.get('code')
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
        'scope': 'identify'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.post('https://discord.com/api/oauth2/token', data=data, headers=headers)
    response_data = response.json()
    access_token = response_data['access_token']

    user_info = requests.get('https://discord.com/api/users/@me', headers={'Authorization': f'Bearer {access_token}'})
    user_info_data = user_info.json()

    user_id = user_info_data['id']
    session['user_id'] = user_id

    # Mark the user as having installed the bot
    asyncio.run(config.user_from_id(user_id).installed.set(True))

    return 'You have successfully logged in and the bot is installed to your profile.'

@app.route('/usercount')
def usercount():
    all_users = asyncio.run(config.all_users())
    installed_users = [user_id for user_id, data in all_users.items() if data['installed']]
    total_installed_users = len(installed_users)
    return f'The total number of users who have installed the bot is: {total_installed_users}'

if __name__ == '__main__':
    try:
        host_ip = sys.argv[1] if len(sys.argv) > 1 else '0.0.0.0'
        app.run(debug=True, host=host_ip, port=5000)
    except Exception as e:
        logging.error(f"Failed to start web server: {e}")
