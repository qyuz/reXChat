import os, xbmcaddon
from common import Debugger
from rechat import CachedService, Message
from twitch import CachedAPI
from ui import ChatRenderer

d = Debugger()

# d.dialog('script started')
addon = xbmcaddon.Addon()
# addon.openSettings()
addonname = addon.getAddonInfo('name')
addonpath = xbmc.translatePath(addon.getAddonInfo('path'))

twitchAPI = CachedAPI()
streamInfo = twitchAPI.getStreamInfo(streamId='v3860959')
rechatService = CachedService(streamInfo)
startMessages = rechatService.next()
messages = map(lambda rm: Message(rm, streamInfo.recordedAtMs), startMessages)

d.dialog(len(messages))
d.dialog(messages[0].absoluteTimeMs)

class PlaybackController():
    def __init__(self):
        pass
    def now(self):
        playerTime = xbmc.Player().getTime() * 1000
        scroll = None
        for message in messages:
            if (message.absoluteTimeMs > playerTime):
                if (scroll != None):
                    chat.scrollToMessage(scroll)
                return
            scroll = message

chat = ChatRenderer()
chat.setMessages(messages)
playback = PlaybackController()
for i in range(100):
    try:
#        d.dialog(i)
        playback.now()
#        chat.scrollToMessage(messages[i * 20])
#        d.dialog(xbmc.Player().getTime())
        xbmc.sleep(200)
    except:
        d.dialog('exception')
chat.hide()
