import os
from flask import Flask, redirect, request, session
import requests
from redbot.core import Config

app = Flask(__name__)
app.secret_key = os.urandom(24)

config = Config.get_conf(None, identifier=1234567892)
config.register_user(installed=False)

@app.route('/')
def home():
    return 'Hello, this is the home page.'

@app.route('/login')
async def login():
    client_id = await config.client_id()
    redirect_uri = await config.redirect_uri()
    scope = 'identify'
    discord_login_url = f'https://discord.com/api/oauth2/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scope}'
    return redirect(discord_login_url)

@app.route('/callback')
async def callback():
    client_id = await config.client_id()
    client_secret = await config.client_secret()
    redirect_uri = await config.redirect_uri()
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
    await config.user_from_id(user_id).installed.set(True)

    return 'You have successfully logged in and the bot is installed to your profile.'

@app.route('/usercount')
async def usercount():
    all_users = await config.all_users()
    installed_users = [user_id for user_id, data in all_users.items() if data['installed']]
    total_installed_users = len(installed_users)
    return f'The total number of users who have installed the bot is: {total_installed_users}'

if __name__ == '__main__':
    app.run(debug=True)
