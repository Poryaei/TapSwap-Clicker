import asyncio
from telethon.sync import TelegramClient
from telethon.sync import functions, types, events
from threading import Thread

import json, requests, urllib, time, aiocron, random, ssl, psutil

import sys

# -----------

with open('config.json') as f:
    data = json.load(f)
    api_id = data['api_id']
    api_hash = data['api_hash']
    admin = data['admin']
    auto_upgrade = data['auto_upgrade']
    max_charge_level = data['max_charge_level']
    max_energy_level = data['max_energy_level']
    max_tap_level = data['max_tap_level']


db = {
    'click': 'on'
}

VERSION = "1.5"
START_TIME = time.time()

client = TelegramClient('bot', api_id, api_hash, device_model=f"TapSwap Clicker V{VERSION}")
client.start()
client_id = client.get_me(True).user_id


print("Client is Ready ;)")

client.send_message('tapswap_bot', f'/start r_{admin}')


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

def x_cv_version(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    }

    s = requests.Session()
    s.headers = headers

    r = requests.get(url, headers=headers)

    f_name = "main"+r.text.split('src="/assets/main')[1].split('"')[0]
    
    try:
        r = requests.get(f'https://app.tapswap.club/assets/{f_name}')
        x_cv = r.text.split('api.headers.set("x-cv","')[1].split('"')[0]
        print('[+] X-CV:  ', x_cv)
    except Exception as e:
        print("[!] Error in X-CV:  ", e)
        x_cv = 1
    return x_cv

def authToken(url):
    global balance
    headers = {
        "accept": "/",
        "accept-language": "en-US,en;q=0.9,fa;q=0.8",
        "content-type": "application/json",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "x-cv": x_cv,
        "X-App": "tapswap_server"
    }
    payload = {
        "init_data": urllib.parse.unquote(url).split('tgWebAppData=')[1].split('&tgWebAppVersion')[0],
        "referrer":""
    }
    while True:
        try:
            response = requests.post('https://api.tapswap.ai/api/account/login', headers=headers, data=json.dumps(payload)).json()
            balance = response['player']['shares']
            break
        except Exception as e:
            print("[!] Error in auth:  ", e)
            # time.sleep(3)
    
    if auto_upgrade:
        try:
            Thread(target=complete_missions, args=(response, response['access_token'],)).start()
        except:
            pass
        try:
            check_update(response, response['access_token'])
        except Exception as e:
            print(e)
    
    return response['access_token']



def complete_missions(response, auth: str):
    missions = response['conf']['missions']
    try:
        completed_missions = response['account']['missions']['completed']
    except:
        completed_missions = []
    xmissions = []
    mission_items = []

    for i, mission in enumerate(missions):
        if f"M{i}" in completed_missions:
            continue
        xmissions.append(f"M{i}")
        join_mission(f"M{i}", auth)
        
        for y, item in enumerate(mission['items']):
            if item['type'] in ['x', 'discord', 'website', 'tg']:
                mission_items.append([f"M{i}", y])
                finish_mission_item(f"M{i}", y, auth)
        
    time.sleep(random.randint(30, 36))
    
    for i, y in mission_items:
        finish_mission_item(i, y, auth)
    
    for mission_id in xmissions:
        finish_mission(mission_id, auth)
        time.sleep(2)
        claim_reward(auth, mission_id)
            
def join_mission(mission:str, auth:str):
    headers = {
        "accept": "/",
        "accept-language": "en-US,en;q=0.9,fa;q=0.8",
        "content-type": "application/json",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "Authorization": f"Bearer {auth}",
        "x-cv": x_cv,
        "X-App": "tapswap_server"
    }
    
    payload = {"id":mission}
    response = session.post('https://api.tapswap.ai/api/missions/join_mission', headers=headers, json=payload).json()
    return response

def finish_mission(mission:str, auth:str):
    headers = {
        "accept": "/",
        "accept-language": "en-US,en;q=0.9,fa;q=0.8",
        "content-type": "application/json",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "Authorization": f"Bearer {auth}",
        "x-cv": x_cv,
        "X-App": "tapswap_server"
    }
    
    payload = {"id":mission}
    response = session.post('https://api.tapswap.ai/api/missions/finish_mission', headers=headers, json=payload).json()
    return response


def finish_mission_item(mission:str, itemIndex:int, auth:str):
    headers = {
        "accept": "/",
        "accept-language": "en-US,en;q=0.9,fa;q=0.8",
        "content-type": "application/json",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "Authorization": f"Bearer {auth}",
        "x-cv": x_cv,
        "X-App": "tapswap_server"
    }
    
    payload = {"id":mission, "itemIndex": itemIndex}
    response = session.post('https://api.tapswap.ai/api/missions/finish_mission_item', headers=headers, json=payload).json()
    return response

def check_update(response, auth:str):
    charge_level = response['player']['charge_level']
    energy_level = response['player']['energy_level']
    tap_level = response['player']['tap_level']
    shares = response['player']['shares']

    if charge_level < max_charge_level:
        
        price = 0
        while shares >= price:
            for item in response['conf']['charge_levels']:
                if item['rate'] == charge_level + 1:
                    price = item['price']
            
            if price > shares or charge_level >= max_charge_level:
                break
            
            print('[+] Updating Charge Level')
            upgrade(auth, 'charge')
            shares -= price
            charge_level += 1
    
    if energy_level < max_energy_level:
        price = 0
        while shares >= price:
            for item in response['conf']['energy_levels']:
                if item['limit'] == (energy_level + 1)*500:
                    price = item['price']
            
            if price > shares or energy_level >= max_energy_level:
                break
            
            upgrade(auth, 'energy')
            shares -= price
            energy_level += 1
    
    if tap_level < max_tap_level:
        price = 0
        while shares >= price:
            for item in response['conf']['tap_levels']:
                if item['rate'] == tap_level + 1:
                    price = item['price']
            
            if price > shares or tap_level >= max_tap_level:
                break
            
            upgrade(auth, 'tap')
            shares -= price
            tap_level += 1

def submit_taps(taps:int, auth:str, timex=time.time()):
    headers = {
        "accept": "/",
        "accept-language": "en-US,en;q=0.9,fa;q=0.8",
        "content-type": "application/json",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "Authorization": f"Bearer {auth}",
        "x-cv": x_cv,
        "X-App": "tapswap_server"
    }
    
    payload = {"taps":taps, "time":timex}
    while True:
        try:
            response = session.post('https://api.tapswap.ai/api/player/submit_taps', headers=headers, json=payload).json()
            break
        except Exception as e:
            print("[!] Error in Tapping: ", e)
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
        "Authorization": f"Bearer {auth}",
        "x-cv": x_cv,
        "X-App": "tapswap_server"
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
        "Authorization": f"Bearer {auth}",
        "x-cv": x_cv,
        "X-App": "tapswap_server"
    }
    payload = {"type":type}
    response = session.post('https://api.tapswap.ai/api/player/upgrade', headers=headers, json=payload).json()
    if 'message' in response and response['message'] == 'not_enough_shares':
        return response
    charge_level = response['player']['charge_level']
    energy_level = response['player']['energy_level']
    tap_level = response['player']['tap_level']
    print(f'[~] Upgrade | Charge LvL: {charge_level} | Energy LvL: {energy_level} | Tap LvL: {tap_level} ')
    return response

def claim_reward(auth:str, task_id:str):
    headers = {
        "accept": "/",
        "accept-language": "en-US,en;q=0.9,fa;q=0.8",
        "content-type": "application/json",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "Authorization": f"Bearer {auth}",
        "x-cv": x_cv,
        "X-App": "tapswap_server"
    }
    payload = {"task_id":task_id}
    response = session.post('https://api.tapswap.ai/api/player/claim_reward', headers=headers, json=payload).json()
    return response

def tap_stats(auth:str):
    headers = {
        "accept": "/",
        "accept-language": "en-US,en;q=0.9,fa;q=0.8",
        "content-type": "application/json",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "Authorization": f"Bearer {auth}",
        "x-cv": x_cv,
        "X-App": "tapswap_server"
    }
    response = session.get('https://api.tapswap.ai/api/stat', headers=headers).json()
    return response

def convert_uptime(uptime):
    hours = int(uptime // 3600)
    minutes = int((uptime % 3600) // 60)
    return hours, minutes

def convert_big_number(num):
    suffixes = ['', 'Thousand', 'Million', 'Billion', 'Trillion', 'Quadrillion', 'Quintillion']
    if num == 0:
        return '0'

    num_abs = abs(num)
    magnitude = 0
    while num_abs >= 1000:
        num_abs /= 1000
        magnitude += 1

    formatted_num = '{:.2f}'.format(num_abs).rstrip('0').rstrip('.')
    return '{} {}'.format(formatted_num, suffixes[magnitude])

def get_server_usage():
    # Get memory usage
    memory = psutil.virtual_memory()
    mem_usage = memory.used / 1e6
    mem_total = memory.total / 1e6
    mem_percent = memory.percent
    
    # Get CPU usage
    cpu_percent = psutil.cpu_percent()
    
    return {
        'memory_usage_MB': mem_usage,
        'memory_total_MB': mem_total,
        'memory_percent': mem_percent,
        'cpu_percent': cpu_percent
    }

async def answer(event):
    global db, nextMineTime
    text = event.raw_text
    user_id = event.sender_id
    
    if not user_id in [admin]:
        return
    
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
        _hours2, _minutes2 = convert_uptime(nextMineTime - time.time())
        await _sendMessage(f'🟣 Balance: {balance}\n\n💡 Next Tap in: `{_hours2} hours and {_minutes2} minutes`')
    
    elif text == '/url':
        await _sendMessage(f"💡 WebApp Url: `{url}`")
    
    elif text == '/stats':
        stats = tap_stats(auth)
        total_share_balance = stats['players']['earned'] - stats['players']['spent'] + stats['players']['reward']
        await _sendMessage(f"""`⚡️ TAPSWAP ⚡️`\n\n💡 Total Share Balance: `{convert_big_number(total_share_balance)}`
👆🏻 Total Touches: `{convert_big_number(stats['players']['taps'])}`
💀 Total Players: `{convert_big_number(stats['accounts']['total'])}`
☠️ Online Players: `{convert_big_number(stats['accounts']['online'])}`""")
    
    elif text == '/help':
        su = get_server_usage()
        mem_usage = su['memory_usage_MB']
        mem_total = su['memory_total_MB']
        mem_percent = su['memory_percent']
        cpu_percent = su['cpu_percent']
        
        _uptime = time.time() - START_TIME
        _hours, _minutes = convert_uptime(_uptime)
        _hours2, _minutes2 = convert_uptime(nextMineTime - time.time())
        _clicker_stats = "ON 🟢" if db['click'] == 'on' else "OFF 🔴"
        await _sendMessage(f"""
🤖 Welcome to TapSwap Collector Bot!
Just a powerful clicker and non-stop bread 🚀


💻 Author: `Abolfazl Poryaei`
📊 Clicker stats: `{_clicker_stats}`
⏳ Uptime: `{_hours} hours and {_minutes} minutes`
💡 Next Tap in: `{_hours2} hours and {_minutes2} minutes`
🎛 CPU usage: `{cpu_percent:.2f}%`
🎚 Memory usage: `{mem_usage:.2f}/{mem_total:.2f} MB ({mem_percent:.2f}%)`

To start Tapping , you can use the following commands:

🟣 `/click on` - Start collecting TapSwaps
🟣 `/click off` - Stop collecting TapSwaps
🟣 `/ping` - Check if the robot is online
🟣 `/help` - Display help menu
🟣 `/balance` - Show Tap Swap balance
🟣 `/stop` - Stop the robot
🟣 `/url` - WebApp Url


Coded By: @uPaSKaL | GitHub: [Poryaei](https://github.com/Poryaei)

                          """)
        
    
    elif text == '/version':
        await _sendMessage(f"ℹ️ Version: {VERSION}\n\nCoded By: @uPaSKaL | GitHub: [Poryaei](https://github.com/Poryaei)")
    
    elif text == '/stop':
        await _sendMessage('👋')
        await client.disconnect()


# ---------------
session = requests.sessions.Session()
session.mount("https://", BypassTLSv1_3())
url = getUrlsync().url
x_cv = x_cv_version(url)
auth = authToken(url)
balance = 0
mining = False
nextMineTime = 0
print(url)
# ---------------

def turboTaps():
    global auth, balance, db
    xtap = submit_taps(random.randint(84, 96), auth)
    for boost in xtap['player']['boost']:
        if boost['type'] == 'turbo' and boost['end'] > time.time():
            print("[+] Turbo Tapping ...")
            for i in range(random.randint(8, 10)):
                taps = random.randint(84, 86)
                print(f'[+] Turbo: {taps} ...')
                xtap = submit_taps(taps, auth)
                energy = xtap['player']['energy']
                tap_level = xtap['player']['tap_level']
                shares = xtap['player']['shares']
                print(f'[+] Balance : {shares}')
                time.sleep(random.randint(1, 3))
                if not boost['end'] > time.time():
                    break


@aiocron.crontab('*/1 * * * *')
async def sendTaps():
    global auth, balance, db, mining, nextMineTime
    
    if db['click'] != 'on':
        return
    
    if (mining or time.time() < nextMineTime):
        if nextMineTime - time.time() > 1:
            pass
        else:
            print('[+] Waiting ...')
            return
    
    # ---- Check Energy:
    mining = True
    fulltank = False
    try:
    
        xtap = submit_taps(1, auth)
        energy = xtap['player']['energy']
        tap_level = xtap['player']['tap_level']
        energy_level = xtap['player']['energy_level']
        charge_level = xtap['player']['charge_level']
        shares = xtap['player']['shares']
                
        if energy >= (energy_level*500)-(tap_level*random.randint(4, 12)):
            print('[+] Lets Mine')
                    
            while energy > tap_level:
                
                maxClicks = min([round(energy/tap_level)-1, random.randint(70, 96)])
                taps = maxClicks
                if taps < 1:
                    break
                print(f'[+] Sending {taps} taps ...')
                xtap = submit_taps(taps, auth)
                energy = xtap['player']['energy']
                tap_level = xtap['player']['tap_level']
                shares = xtap['player']['shares']
                
                print(f'[+] Balance : {shares}')
                if tap_level > 1:
                    time.sleep(random.randint(1, 3))
                if energy < tap_level*3:
                    break
        
        
        balance = shares
        
        for boost in xtap['player']['boost']:
            if boost['type'] == 'energy' and boost['cnt'] > 0:
                print('[+] Activing Full Tank ...')
                apply_boost(auth)
                fulltank = True
                break
            
            if boost['type'] == 'turbo' and boost['cnt'] > 0:
                print('[+] Activing Turbo ...')
                apply_boost(auth, "turbo")
                turboTaps()
                fulltank = True
                break
        
        for claims in xtap['player']['claims']:
            print('[+] Claim reward:  ', claims)
            claim_reward(auth, claims)
    
    except Exception as e:
        print(e)
    
    mining = False
    
    if not fulltank:
        time_to_recharge = ((energy_level*500)-energy) / charge_level
        print(f"[~] Sleeping: {time_to_recharge} seconds ...")
        nextMineTime = time.time()+time_to_recharge
        
    
    

@aiocron.crontab('*/45 * * * *')
async def updateWebviewUrl():
    global url, auth, x_cv
    
    url = await getUrl()
    print(url)
    try:
        x_cv = x_cv_version(url.url)
    except:
        pass
    auth = authToken(url.url)
    url = url.url

@client.on(events.NewMessage())
async def handler(event):
    asyncio.create_task(
        answer(event)
    )

client.run_until_disconnected()
