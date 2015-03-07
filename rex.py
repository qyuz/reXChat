import os, xbmc, xbmcaddon
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
        self.scrolled = None
        self.chatRows = 28
        self.prependLines = None
        self.prependMessages = None
        self.fetchedStart = None
        self.fetchedEnd = None
        self.renderedStart = None
        self.renderedEnd = None
        self.twitchAPI = CachedAPI()
        self.rechatService = CachedService()
    def clearChat(self):
        self.scrolled = None
        self.renderedStart = None
        self.renderedEnd = None
        self.chat.clear()
    def fetchMessages(self):
        rMessages, start, end = self.rechatService.nextWithRange()
        if(len(self.prependMessages) > 0):
            self.fetchedStart = self.toPlayerTime(self.prependMessages[0].receivedAtMs)
        else:
            self.fetchedStart = self.toPlayerTime(start)
        self.fetchedEnd = self.toPlayerTime(end)
        self.messages = self.prependMessages + map(lambda rm: Message(rm, self.streamInfo.recordedAtMs), rMessages)
        return len(self.messages)
    def getStreamInfo(self):
        self.streamInfo = self.twitchAPI.getStreamInfo(streamId='v3860959')
        self.rechatService.setStreamInfo(self.streamInfo)
    def isFetched(self, playerTime):
        playerTime = playerTime * 1000
        return playerTime >= self.fetchedStart and playerTime <= self.fetchedEnd
    def isRendered(self, playerTime):
        playerTime = playerTime * 1000
        return playerTime >= self.renderedStart and playerTime <= self.renderedEnd
    def onSettingsChanged(self):
        self.settings['outdated'] = True
    def preparePrepend(self):
        if(self.scrolled == None):
            self.prependLines = [''] * self.chatRows
            self.prependMessages = []
            return
        linesSeen = []
        messagesNotSeen = []
        foundScrolled = False
        i = -1
        while(len(linesSeen) < self.chatRows):
            message = self.messages[i]
            i = i - 1
            lines = message.getLines()
            if(message.id == self.scrolled.id or foundScrolled == True):
                foundScrolled = True
                linesSeen = lines + linesSeen
            else:
                messagesNotSeen.insert(0, message)
        self.prependLines = linesSeen[-self.chatRows:]
        self.prependMessages = messagesNotSeen
    def render(self):
        self.chat.addLines(self.prependLines)
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
                    self.scrolled = scroll
                return
            scroll = message
    def stop(self):
        self.chat.hide()
    def updateSettings(self):
        self.settings.update()
        self.settings['outdated'] = False
    def toPlayerTime(self, receivedAtMs):
        return receivedAtMs - self.streamInfo.recordedAtMs

playback = PlaybackController()
playback.getStreamInfo()
for i in range(100):
    playerTime = xbmc.Player().getTime()
    fetched = playback.isFetched(playerTime)
    rendered = playback.isRendered(playerTime)
    if(fetched == False):
        playback.preparePrepend()
        playback.fetchMessages()
    if(fetched == True and rendered == False):
        playback.clearChat()
        playback.render()
    if(rendered == True):
        playback.scroll(playerTime)
    xbmc.sleep(200)
playback.stop()
