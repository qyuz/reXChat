import os, xbmcaddon
from common import Debugger
from rechat import CachedService, Message
from twitch import CachedAPI
from ui import ChatRenderer

d = Debugger()

addon = xbmcaddon.Addon()
# addon.openSettings()
addonname = addon.getAddonInfo('name')
addonpath = xbmc.translatePath(addon.getAddonInfo('path'))

class Settings():
    def __init__(self):
        self.update()
    def update(self):
        self.backgroundX = int(addon.getSetting('backgroundX'))
        self.backgroundY = int(addon.getSetting('backgroundY'))
        self.backgroundWidth = int(addon.getSetting('backgroundWidth'))
        self.backgroundHeight = int(addon.getSetting('backgroundHeight'))
        self.backgroundOpacity = addon.getSetting('backgroundOpacity')
        self.chatX = int(addon.getSetting('chatX'))
        self.chatY = int(addon.getSetting('chatY'))
        self.chatWidth = int(addon.getSetting('chatWidth'))
        self.chatHeight = int(addon.getSetting('chatHeight'))
        self.characters = int(addon.getSetting('characters'))
        self.delay = int(addon.getSetting('delay')) * 1000

class PlaybackController(xbmc.Monitor):
    def __init__(self):
        self.settings = Settings()
        self.chat = ChatRenderer()
        self.fetchedStart = None
        self.fetchedEnd = None
        self.renderedStart = None
        self.renderedEnd = None
        self.twitchAPI = CachedAPI()
        self.rechatService = CachedService()
    def fetchMessages(self):
        rMessages, start, end = self.rechatService.nextWithRange()
        self.fetchedStart = start - self.streamInfo.recordedAtMs
        self.fetchedEnd = end - self.streamInfo.recordedAtMs
        self.messages = map(lambda rm: Message(rm, self.streamInfo.recordedAtMs), rMessages)
        return len(self.messages)
    def getStreamInfo(self):
        self.streamInfo = self.twitchAPI.getStreamInfo(streamId='v3860959')
        self.rechatService.setStreamInfo(self.streamInfo)
    def isRendered(self, playerTime):
        playerTime = playerTime * 1000
        return playerTime >= self.renderedStart and playerTime <= self.renderedEnd
    def onSettingsChanged(self):
        self.settings['outdated'] = True
    def render(self):
        self.chat.addMessages(self.messages)
        self.renderedStart = self.fetchedStart
        self.renderedEnd = self.fetchedEnd
    def scroll(self, playerTime):
        playerTime = playerTime * 1000
        scroll = None
        for message in self.messages:
            if (message.absoluteTimeMs > playerTime):
                if (scroll != None):
                    self.chat.scrollToMessage(scroll)
                return
            scroll = message
    def stop(self):
        self.chat.hide()
    def updateSettings(self):
        self.settings.update()
        self.settings['outdated'] = False

playback = PlaybackController()
playback.getStreamInfo()
playback.fetchMessages()
d.dialog(playback.renderedStart)
d.dialog(playback.renderedEnd)
d.dialog(playback.isRendered(xbmc.Player().getTime()))
playback.render()
d.dialog(playback.isRendered(xbmc.Player().getTime()))
for i in range(100):
    try:
#        d.dialog(i)
        playback.scroll(xbmc.Player().getTime())
        xbmc.sleep(200)
    except:
        d.dialog('exception')
playback.stop()
