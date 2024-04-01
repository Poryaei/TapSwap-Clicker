import asyncio
from telethon.sync import TelegramClient
from telethon.sync import functions, types, events

import json, requests, urllib, time, aiocron, random
# -----------
with open('config.json') as f:
    data = json.load(f)
    api_id = data['api_id']
    api_hash = data['api_hash']
    admin = data['admin']

db = {
    'click': 'on'
}

VERSION = "1.0"
START_TIME = time.time()

client = TelegramClient('bot', api_id, api_hash, device_model=f"TapSwap Clicker V{VERSION}")
client.start()
client_id = client.get_me(True).user_id


print("Client is Ready ;)")

# -----------


def getUrlsync():
    return client(
        functions.messages.RequestWebViewRequest(
            peer='tapswap_bot',
            bot='tapswap_bot',
            platform='ios',
            from_bot_menu=False,
            url='https://app.tapswap.ai/',
        )
    )

async def getUrl():
    return await client(
        functions.messages.RequestWebViewRequest(
            peer='tapswap_bot',
            bot='tapswap_bot',
            platform='ios',
            from_bot_menu=False,
            url='https://app.tapswap.ai/',
        )
    )

def authToken(url):
    headers = {
        "accept": "/",
        "accept-language": "en-US,en;q=0.9,fa;q=0.8",
        "content-type": "application/json",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "x-cv": "323"
    }
    payload = {
        "init_data": urllib.parse.unquote(url).split('tgWebAppData=')[1].split('&tgWebAppVersion')[0],
        "referrer":""
    }
    response = requests.post('https://api.tapswap.ai/api/account/login', headers=headers, data=json.dumps(payload)).json()

    return response['access_token']


def submit_taps(taps:int, auth:str, timex=time.time()):
    headers = {
        "accept": "/",
        "accept-language": "en-US,en;q=0.9,fa;q=0.8",
        "content-type": "application/json",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "Authorization": f"Bearer {auth}"
    }
    
    payload = {"taps":taps, "time":timex}
    response = requests.post('https://api.tapswap.ai/api/player/submit_taps', headers=headers, json=payload).json()
    # Energy: response['player']['energy']
    return response

def apply_boost(auth:str, type:str="energy"):
    headers = {
        "accept": "/",
        "accept-language": "en-US,en;q=0.9,fa;q=0.8",
        "content-type": "application/json",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "Authorization": f"Bearer {auth}"
    }
    payload = {"type":type}
    response = requests.post('https://api.tapswap.ai/api/player/apply_boost', headers=headers, json=payload).json()
    return response

def convert_uptime(uptime):
    hours = int(uptime // 3600)
    minutes = int((uptime % 3600) // 60)
    return hours, minutes


async def answer(event):
    global db
    text = event.raw_text
    user_id = event.sender_id
    
    if admin == client_id:
        _sendMessage = event.edit
    else:
        _sendMessage = event.reply
    
    if text == '/ping':
        await _sendMessage('👽')
    
    elif text.startswith('/click '):
        stats = text.split('/click ')[1]
        if not stats in ['off', 'on']:
            await _sendMessage('❌ Bad Command!')
            return
        
        db['click'] = stats
        if stats == 'on':
            await _sendMessage('✅ Mining Started!')
        else:
            await _sendMessage('💤 Mining turned off!')
    
    elif text == '/balance':
        await _sendMessage(f'🟣 Balance: {balance}')
    
    elif text == '/help':
        _uptime = time.time() - START_TIME
        _hours, _minutes = convert_uptime(_uptime)
        _clicker_stats = "ON 🟢" if db['click'] == 'on' else "OFF 🔴"
        await _sendMessage(f"""
🤖 Welcome to TapSwap Collector Bot!
Just a powerful clicker and non-stop bread 🚀


💻 Author: `Abolfazl Poryaei`
📊 Clicker stats: `{_clicker_stats}`
⏳ Uptime: `{_hours} hours and {_minutes} minutes`

To start Tapping , you can use the following commands:

🟣 `/click on` - Start collecting Not Coins
🟣 `/click off` - Stop collecting Not Coins
🟣 `/ping` - Check if the robot is online
🟣 `/help` - Display help menu
🟣 `/balance` - Show Tap Swap balance
🟣 `/stop` - Stop the robot


Coded By: @uPaSKaL | GitHub: [Poryaei](https://github.com/Poryaei)

                          """)
        
    
    elif text == '/version':
        await _sendMessage(f"ℹ️ Version: {VERSION}")
    
    elif text == '/stop':
        await _sendMessage('👋')
        await client.disconnect()


# ---------------
url = getUrlsync().url
auth = authToken(url)
balance = 0
# ---------------

@aiocron.crontab('*/1 * * * *')
async def sendTaps():
    global auth, balance, db
    
    if db['click'] != 'on':
        return
    
    print('[+] Lets Mine')
    # ---- Check Energy:
    xtap = submit_taps(1, auth)
    energy = xtap['player']['energy']
    tap_level = xtap['player']['tap_level']
    energy_level = xtap['player']['energy_level']
    shares = xtap['player']['shares']
    
    if energy >= (energy_level*500)-(tap_level*random.randint(2, 4)):
        
        while energy > tap_level:
            
            maxClicks = min([round(energy/tap_level)-1, random.randint(70, 80)])
            try:
                taps = random.randint(random.randint(1, 10), random.randint(11, maxClicks))
            except:
                taps = maxClicks
            
            print(f'[+] Sending {taps} ...')
            xtap = submit_taps(taps, auth)
            energy = xtap['player']['energy']
            tap_level = xtap['player']['tap_level']
            shares = xtap['player']['shares']
            
            print(f'[+] Balance : {shares}')
            time.sleep(random.randint(0, round(60/taps)))
    else:
        print('[~] Waiting For Full Tank')
    
    for boost in xtap['player']['boost']:
        if boost['type'] == 'energy' and boost['cnt'] > 0:
            print('[+] Activing Full Tank ...')
            apply_boost(auth)
                
    balance = shares
    

@aiocron.crontab('*/15 * * * *')
async def updateWebviewUrl():
    global url, auth
    
    url = await getUrl().url
    auth = authToken(url)

@client.on(events.NewMessage())
async def handler(event):
    asyncio.create_task(
        answer(event)
    )

client.run_until_disconnected()
