import functools, os, xbmc, xbmcaddon
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
        addon = xbmcaddon.Addon()
        self.backgroundX = int(addon.getSetting('backgroundX'))
        self.backgroundY = int(addon.getSetting('backgroundY'))
        self.backgroundWidth = int(addon.getSetting('backgroundWidth'))
        self.backgroundHeight = int(addon.getSetting('backgroundHeight'))
        self.backgroundOpacity = addon.getSetting('backgroundOpacity')
        self.chatX = int(addon.getSetting('chatX'))
        self.chatY = int(addon.getSetting('chatY'))
        self.chatWidth = int(addon.getSetting('chatWidth'))
        self.chatHeight = int(addon.getSetting('chatHeight'))
        self.chatLineHeight = int(addon.getSetting('chatLineHeight'))
        self.fontSize = 'font%s' %addon.getSetting('fontSize')
        self.characters = int(addon.getSetting('characters'))
        self.delay = int(addon.getSetting('delay')) * 1000
        self.updated = True

class PlaybackController(xbmc.Monitor):
    def __init__(self):
        self.settings = Settings()
        self.chat = ChatRenderer()
        self.messages = None
        self.rendered = False
        self.chatRows = int(self.settings.chatHeight / self.settings.chatLineHeight)
        self.prependLines = None
        self.fetchedStart = None
        self.fetchedEnd = None
        self.twitchAPI = CachedAPI()
        self.rechatService = CachedService()
        self.applySettings()
    def _fetch(self, fetch):
        self.rendered = False
        rMessages, start, end = fetch()
        self.fetchedStart = self.toPlayerTime(start)
        self.fetchedEnd = self.toPlayerTime(end)
        self.messages = map(lambda rm: Message(rm, self.streamInfo.recordedAtMs), rMessages)
        return len(self.messages)
    def applySettings(self):
        self.chat.resizeBackground(self.settings.backgroundX, self.settings.backgroundY, self.settings.backgroundWidth, self.settings.backgroundHeight)
        self.chat.resizeChat(self.settings.chatX, self.settings.chatY, self.settings.chatWidth, self.settings.chatHeight)
    def clearChat(self):
        self.rendered = False
        self.chat.clear()
    def fetchAfter(self, playerTimeMs):
        afterMs = self.fromPlayerTime(playerTimeMs)
        fetch = functools.partial(self.rechatService.afterMsWithRange, afterMs)
        return self._fetch(fetch)
    def fetchNext(self):
        return self._fetch(self.rechatService.nextWithRange)
    def fromPlayerTime(self, playerTimeMs):
        return int(self.streamInfo.recordedAtMs + playerTimeMs)
    def getPlayerTime(self):
        return int(xbmc.Player().getTime() * 1000)
    def getStreamInfo(self):
        self.streamInfo = self.twitchAPI.getStreamInfo(streamId='v3860959')
        self.rechatService.setStreamInfo(self.streamInfo)
    def isFetched(self, playerTimeMs):
        return playerTimeMs >= self.fetchedStart and playerTimeMs <= self.fetchedEnd
    def isFetchedBoundsEpsilon(self, playerTimeMs):
        isFetched = self.isFetched(playerTimeMs)
        beforeStart = playerTimeMs - playback.fetchedStart
        afterEnd = playerTimeMs - playback.fetchedEnd
        return isFetched, beforeStart, afterEnd
    def onSettingsChanged(self):
        self.settings.updated = False
    def preparePrepend(self):
        if(self.rendered == False):
            self.prependLines = [''] * self.chatRows
            return
        lastLines = []
        i = -1
        while(len(lastLines) < self.chatRows):
            message = self.messages[i]
            i = i - 1
            lastLines = message.getLines() + lastLines
        self.prependLines = lastLines[-self.chatRows:]
    def render(self):
        self.chat.addLines(self.prependLines)
        self.chat.addMessages(self.messages)
        self.rendered = True
    def scroll(self, playerTimeMs):
        if (self.rendered == True):
            scroll = None
            for message in self.messages:
                if (message.absoluteTimeMs > playerTimeMs):
                    if (scroll != None):
                        self.chat.scrollToMessage(scroll)
                    return
                scroll = message
            self.chat.scrollToMessage(scroll)
    def stop(self):
        self.chat.hide()
    def updateSettings(self):
        self.settings.update()
    def toPlayerTime(self, receivedAtMs):
        return receivedAtMs - self.streamInfo.recordedAtMs

playback = PlaybackController()
playback.getStreamInfo()
playback.fetchNext()
playback.preparePrepend()
for i in range(100):
    if(playback.settings.updated == False):
        playback.updateSettings()
        playback.applySettings()
    playerTimeMs = playback.getPlayerTime()
    isFetched, beforeFetchedRange, afterFetchedRange = playback.isFetchedBoundsEpsilon(playerTimeMs)
    playback.scroll(playerTimeMs)
    if(isFetched == False):
        if(beforeFetchedRange < 0 or afterFetchedRange > 900000):
#            d.dialog('doing after because beforeFetchedRange: [%s]\nafterFetchedRange: [%s]' %(beforeFetchedRange, afterFetchedRange))
            playback.clearChat()
            playback.preparePrepend()
            playback.fetchAfter(playerTimeMs)
        else:
#            d.dialog('doing next because beforeFetchedRange: [%s]\nafterFetchedRange: [%s]' %(beforeFetchedRange, afterFetchedRange))
            playback.preparePrepend()
            playback.clearChat()
            playback.fetchNext()
        isFetched = True #ensures rapid render
    if(isFetched == True and playback.rendered == False):
#        d.dialog('rendering')
        playback.render()
    xbmc.sleep(200)
playback.stop()
