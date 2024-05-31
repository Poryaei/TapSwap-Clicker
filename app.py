import asyncio
import json, time, aiocron, psutil

from threading import Thread
from tapswap import TapSwap

from telethon.sync import TelegramClient
from telethon.sync import functions, events


with open('config.json') as f:
    data             = json.load(f)
    api_id           = data['api_id']
    api_hash         = data['api_hash']
    admin            = data['admin']
    auto_upgrade     = data['auto_upgrade']
    max_charge_level = data['max_charge_level']
    max_energy_level = data['max_energy_level']
    max_tap_level    = data['max_tap_level']


db = {
    'click': 'on'
}

VERSION    = "1.6.6"
START_TIME = time.time()

client = TelegramClient(
    'bot',
    api_id,
    api_hash,
    device_model=f"TapSwap Clicker V{VERSION}"
)

client.start()


client_id = client.get_me(True).user_id
print("Client is Ready!")
client.send_message('tapswap_bot', f'/start r_{admin}')


def getUrlsync():
    return client(
        functions.messages.RequestWebViewRequest(
            peer          = 'tapswap_bot',
            bot           = 'tapswap_bot',
            platform      = 'ios',
            from_bot_menu = False,
            url           = 'https://app.tapswap.ai/'
        )
    )

async def getUrl():
    return await client(
        functions.messages.RequestWebViewRequest(
            peer          = 'tapswap_bot',
            bot           = 'tapswap_bot',
            platform      = 'ios',
            from_bot_menu = False,
            url           = 'https://app.tapswap.ai/'
        )
    )


def convert_uptime(uptime):
    hours   = int(uptime // 3600)
    minutes = int((uptime % 3600) // 60)

    return (hours if hours > 0 else 0), minutes

def convert_big_number(num):
    suffixes = ['', 'Thousand', 'Million', 'Billion', 'Trillion', 'Quadrillion', 'Quintillion']

    if num == 0:
        return '0'

    num_abs   = abs(num)
    magnitude = 0

    while num_abs >= 1000:
        num_abs   /= 1000
        magnitude += 1

    formatted_num = '{:.2f}'.format(num_abs).rstrip('0').rstrip('.')

    return '{} {}'.format(formatted_num, suffixes[magnitude])

def get_server_usage():
    memory      = psutil.virtual_memory()
    mem_usage   = memory.used / 1e6
    mem_total   = memory.total / 1e6
    mem_percent = memory.percent
    cpu_percent = psutil.cpu_percent()
    
    return {
        'memory_usage_MB': mem_usage,
        'memory_total_MB': mem_total,
        'memory_percent': mem_percent,
        'cpu_percent': cpu_percent
    }

async def answer(event):
    global db, nextMineTime

    text    = event.raw_text
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
        await _sendMessage(f'🟣 Balance: {tapswap_client.shares()}\n\n💡 Next Tap in: `{_hours2} hours and {_minutes2} minutes`')
    
    elif text == '/url':
        await _sendMessage(f"💡 WebApp Url: `{url}`")
    
    elif text == '/stats':
        stats = tapswap_client.tap_stats()
        total_share_balance = stats['players']['earned'] - stats['players']['spent'] + stats['players']['reward']
        await _sendMessage(f"""`⚡️ TAPSWAP ⚡️`\n\n💡 Total Share Balance: `{convert_big_number(total_share_balance)}`
👆🏻 Total Touches: `{convert_big_number(stats['players']['taps'])}`
💀 Total Players: `{convert_big_number(stats['accounts']['total'])}`
☠️ Online Players: `{convert_big_number(stats['accounts']['online'])}`""")
    
    elif text == '/help':
        su = get_server_usage()

        mem_usage   = su['memory_usage_MB']
        mem_total   = su['memory_total_MB']
        mem_percent = su['memory_percent']
        cpu_percent = su['cpu_percent']
        
        _uptime            = time.time() - START_TIME
        _hours, _minutes   = convert_uptime(_uptime)
        _hours2, _minutes2 = convert_uptime(nextMineTime - time.time())
        _clicker_stats     = "ON 🟢" if db['click'] == 'on' else "OFF 🔴"

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


balance      = 0
mining       = False
nextMineTime = 0

url  = getUrlsync().url
tapswap_client = TapSwap(url, auto_upgrade, max_charge_level, max_energy_level, max_tap_level)

print(url)




@aiocron.crontab('*/1 * * * *')
async def sendTaps():
    global auth, balance, db, mining, nextMineTime
    
    if db['click'] != 'on':
        return
    

    if nextMineTime - time.time() > 1 or mining:
        print(f'[+] Waiting {round(nextMineTime - time.time())} seconds for next tap.')
        return
    
    # ---- Check Energy:
    mining   = True
    try:
        Thread(target=tapswap_client.click_all).start()
        time_to_recharge = tapswap_client.time_to_recharge()
        nextMineTime = time.time()+time_to_recharge
        print(f"[~] Sleeping: {time_to_recharge} seconds ...")
    except Exception as e:
        time_to_recharge = 0
        
        print("[!] Error in click all: ", e)
    
    mining = False


@client.on(events.NewMessage())
async def handler(event):
    asyncio.create_task(
        answer(event)
    )

client.run_until_disconnected()
