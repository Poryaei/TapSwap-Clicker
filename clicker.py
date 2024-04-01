import asyncio
from telethon.sync import TelegramClient
from telethon.sync import functions, types, events

import json, requests, urllib, time, aiocron, random, ssl

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

client = TelegramClient('main', api_id, api_hash, device_model=f"TapSwap Clicker V{VERSION}")
client.start()
client_id = client.get_me(True).user_id


print("Client is Ready ;)")

# -----------

class BypassTLSv1_3(requests.adapters.HTTPAdapter):
    SUPPORTED_CIPHERS = [
        "ECDHE-ECDSA-AES128-GCM-SHA256", "ECDHE-RSA-AES128-GCM-SHA256",
        "ECDHE-ECDSA-AES256-GCM-SHA384", "ECDHE-RSA-AES256-GCM-SHA384",
        "ECDHE-ECDSA-CHACHA20-POLY1305", "ECDHE-RSA-CHACHA20-POLY1305",
        "ECDHE-RSA-AES128-SHA", "ECDHE-RSA-AES256-SHA",
        "AES128-GCM-SHA256", "AES256-GCM-SHA384", "AES128-SHA", "AES256-SHA", "DES-CBC3-SHA",
        "TLS_AES_128_GCM_SHA256", "TLS_AES_256_GCM_SHA384", "TLS_CHACHA20_POLY1305_SHA256",
        "TLS_AES_128_CCM_SHA256", "TLS_AES_256_CCM_8_SHA256"
    ]

    def __init__(self, *args, **kwargs):
        self.ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        self.ssl_context.set_ciphers(':'.join(BypassTLSv1_3.SUPPORTED_CIPHERS))
        self.ssl_context.set_ecdh_curve("prime256v1")
        self.ssl_context.minimum_version = ssl.TLSVersion.TLSv1_3
        self.ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3
        super().__init__(*args, **kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs["ssl_context"] = self.ssl_context
        kwargs["source_address"] = None
        return super().init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        kwargs["ssl_context"] = self.ssl_context
        kwargs["source_address"] = None
        return super().proxy_manager_for(*args, **kwargs)


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
    response = session.post('https://api.tapswap.ai/api/player/submit_taps', headers=headers, json=payload).json()
    # Energy: response['player']['energy']
    return response

def apply_boost(auth:str, type:str="energy"):
    # Types: turbo, energy
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
    response = session.post('https://api.tapswap.ai/api/player/apply_boost', headers=headers, json=payload).json()
    return response

def upgrade(auth:str, type:str="charge"):
    # Types: energy, tap, charge
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
    response = session.post('https://api.tapswap.ai/api/player/apply_boost', headers=headers, json=payload).json()
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
session = requests.sessions.Session()
session.mount("https://", BypassTLSv1_3())
url = getUrlsync().url
auth = authToken(url)
balance = 0
mining = False
print(url)
# ---------------

def turboTaps():
    global auth, balance, db
    
    xtap = submit_taps(1, auth)
    for boost in xtap['player']['boost']:
        if boost['type'] == 'turbo' and boost['end'] > time.time():
            print("[+] Turbo Tapping ...")
            for i in range(random.randint(8, 14)):
                taps = random.randint(80, 84)
                print(f'[+] Turbo: {taps} ...')
                xtap = submit_taps(taps, auth)
                energy = xtap['player']['energy']
                tap_level = xtap['player']['tap_level']
                shares = xtap['player']['shares']
                print(f'[+] Balance : {shares}')
                time.sleep(random.randint(0, round(60/taps)+random.randint(1, 3)))
            
@aiocron.crontab('*/2 * * * *')
async def sendTaps():
    global auth, balance, db, mining
    
    if db['click'] != 'on':
        return
    
    if mining:
        return
    
    # ---- Check Energy:
    mining = True
    xtap = submit_taps(1, auth)
    energy = xtap['player']['energy']
    tap_level = xtap['player']['tap_level']
    energy_level = xtap['player']['energy_level']
    shares = xtap['player']['shares']
    
    if energy >= (energy_level*500)-(tap_level*random.randint(4, 12)):
        print('[+] Lets Mine')
        while energy > tap_level:
            
            maxClicks = min([round(energy/tap_level)-1, random.randint(70, 80)])
            try:
                taps = random.randint(random.randint(1, 10), random.randint(11, maxClicks))
            except:
                taps = maxClicks
            if taps < 1:
                break
            print(f'[+] Sending {taps} ...')
            xtap = submit_taps(taps, auth)
            energy = xtap['player']['energy']
            tap_level = xtap['player']['tap_level']
            shares = xtap['player']['shares']
            
            print(f'[+] Balance : {shares}')
            print(energy, tap_level)
            time.sleep(random.randint(0, round(60/taps)))

    
    balance = shares
    
    for boost in xtap['player']['boost']:
        if boost['type'] == 'energy' and boost['cnt'] > 0:
            print('[+] Activing Full Tank ...')
            apply_boost(auth)
            break
        
        if boost['type'] == 'turbo' and boost['cnt'] > 0:
            print('[+] Activing Turbo ...')
            apply_boost(auth, "turbo")
            turboTaps()
            break
    
    mining = False
    
    

@aiocron.crontab('*/15 * * * *')
async def updateWebviewUrl():
    global url, auth
    
    url = await getUrl()
    print(url)
    auth = authToken(url.url)

@client.on(events.NewMessage())
async def handler(event):
    asyncio.create_task(
        answer(event)
    )

client.run_until_disconnected()
