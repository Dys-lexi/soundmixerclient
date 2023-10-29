from pycaw.pycaw import AudioUtilities
import random
import requests
import time
import colorgetter
import asyncio
import socketio
import random
import keyboard
USERNAME = "pff"
PASSWORD = "pffed"

# case specific application names btw (exe name but without .exe)
keys = ["page up", "page down", "home", "end", "insert", "delete"]
keylinks = ["games", "browsers", "chats"]
hotkeys = {"browsers": ["waterfox", "firefox", "chrome"], "games": ["Terraria", "dotnet", "r5apex", "FSD-Win64-Shipping",
                                                                    "Titanfall2", "Overwatch", "OuterWilds", "hl2","Discovery", "AShortHike", "factorio", "Goose Goose Duck"], "chats": ["Discord", "DiscordPTB"]}


sessions = False

token = False
sio = socketio.AsyncClient()#reconnection=True, reconnection_attempts=22222, reconnection_delay=1, reconnection_delay_max=5)




async def mouseconnect():
    global token
    try:
        req = requests.post('https://xixya.com/api/log',
                            json={"username": USERNAME, "password": PASSWORD}, timeout=8)

        req = req.json()
    except Exception as e:
        print(e)
        time.sleep(1)
        return
    print("login status:", req["message"])
    if req["message"] != "ok":
        time.sleep(1)
        print(req["message"])

    token = req["token"]
    req = requests.post('https://xixya.com/api/mixerhotkeys',
                        json={"token": token, "hotkeys": hotkeys}, timeout=8)
    req = req.json()
    if req["message"] != "ok":
        print(req["message"])
    else:
        print("hotkeys set")
    try:
        await sio.connect('https://xixya.com', socketio_path='/api/socket.io/')
    except socketio.exceptions.ConnectionError as e:
        print(f"Connection error: {e}")
    await sio.emit("/api/connect", "mixerclient")
    await sio.emit("/api/roominit", {'id': token})
    print("Connected!")

    # await sio.emit("/api/audioset",{"token":token,"audio":{"waterfox":"100"}})
@sio.event
async def disconnect():
    print("Disconnected from server.")
    await attempt_reconnect()

async def attempt_reconnect():
    while True:
        try:
            print("Attempting to reconnect...")
            await mouseconnect()
            break
        except Exception as e:
            print(f"Reconnection failed: {e}")
            await asyncio.sleep(5)

@sio.on("setvolume")
def setvolume(volume):

    w = getaudioinfo()
    apps = {}
    names = []
    for app in w:
        names.append(app.Process.name())
    levels = volume

    convertedlevels = {}
    for i in range(len(levels)):
        convertedlevels[list(levels.keys())[i] +
                        ".exe"] = levels[list(levels.keys())[i]]
    levels = convertedlevels
    print(levels)

    indexes = {}
    for i in range(len(names)):
        for j in range(len(levels)):
            if list(levels.keys())[j] == names[i]:
                indexes[i] = (levels[list(levels.keys())[j]])
    setvols(indexes, w)


async def waitforkey(keys):
    # browsers, chats, games
    b = 0
    while b not in keys:
        b = await asyncio.to_thread(keyboard.read_key)
    return b


async def macrokeys():
    mutliplier = 1
    while True:
        key = await asyncio.create_task(waitforkey(keys))
        target = False
        increment = 0
        startedat = time.time()
        try:
            if startedat - lasttime < 0.28:
                mutliplier += 1
            else:
                mutliplier = 1
        except:
            pass
        for i in range(len(keys)):
            if keys[i] == key:
                target = keylinks[i//2]
                increment = ((((i % 2)-1)*-1)*2-1)*mutliplier

        await sio.emit("/api/incrementmixer", {"token": token, "target": target, "increment": increment})
        lasttime = startedat
        await asyncio.sleep(0.15)


def set_mixer_level(session, volume):
    volume_control = session.SimpleAudioVolume

    volume_control.SetMasterVolume(volume, None)


def getaudioinfo():
    sessions = AudioUtilities.GetAllSessions()
    running_apps = []
    for session in sessions:
        if session.Process and session.Process.name():
            running_apps.append(session)
    return running_apps


def setvols(indexes, w):
    d = []
    for i in w:
        d.append(i.Process.name())
    for index in range(len(w)):
        if hasattr(w[index], 'SimpleAudioVolume'):
            volume_control = w[index].SimpleAudioVolume
            try:
                set_mixer_level(w[index], round(int(indexes[index]) / 100, 2))
            except:
                pass
        else:
            print("Volume control not available for", w[index])


colors = {}


async def main():
    global sessions
    asyncio.create_task(mouseconnect())
    asyncio.create_task(macrokeys())
    await asyncio.sleep(5)
    failed = False
    while True:
        w = getaudioinfo()
        apps = {}
        names = []
        for app in w:
            if app.Process.name() not in list(colors.keys()):
                colors[app.Process.name()] = colorgetter.get_most_common_color(
                    app.Process.exe())

            if colors[app.Process.name()] != (-2, -1, -1):
                apps[app.Process.name().split(".exe")[0]] = [round(
                    app.SimpleAudioVolume.GetMasterVolume(), 2), colors[app.Process.name()]]
            names.append(app.Process.name())
        try:
            r = requests.post('https://xixya.com/api/mixerargs',
                              json={"apps": apps, "token": token, "type": "endclient"}, timeout=6)
                   
            if r.json()["message"] != "ok" or failed == True:
                failed = True
                print(r.json()["message"])
                d += 1
        except Exception as e:
            print("cannot send request to server")
            if failed:
                print("http reconnected, starting socket reconnect")
                await asyncio.sleep(1)
                await sio.disconnect()

                await asyncio.sleep(5)
                # sio.clear()
                # sio = socketio.AsyncClient()
                asyncio.create_task(mouseconnect())
                print("socket reattempt finished")
                failed = False
            else:
                print("waiting for succsesful http to reconnect")
                failed = True
        await asyncio.sleep(5)

asyncio.run(main())

asyncio.run(clientcomms())
