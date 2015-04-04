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
        self.updated = False
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
        self.fetchedStart = None
        self.fetchedEnd = None
        self.twitchAPI = CachedAPI()
        self.rechatService = CachedService()
    def _fetch(self, fetch):
        self.rendered = False
        rMessages, start, end = fetch()
        self.fetchedStart = self.toPlayerTime(start)
        self.fetchedEnd = self.toPlayerTime(end)
        self.messages = map(lambda rm: Message(rm, self.streamInfo.recordedAtMs), rMessages)
        return len(self.messages)
    def applySettings(self):
        self.chat.resizeBackground(self.settings.backgroundX, self.settings.backgroundY, self.settings.backgroundWidth, self.settings.backgroundHeight)
        self.chat.resizeChat(self.settings.chatX, self.settings.chatY, self.settings.chatWidth, self.settings.chatHeight, self.settings.chatLineHeight)
        Message.lineLength = self.settings.characters
    def fetchAfter(self, playerTimeMs):
        afterMs = self.fromPlayerTime(playerTimeMs)
        fetch = functools.partial(self.rechatService.afterMsWithRange, afterMs)
        return self._fetch(fetch)
    def fetchStart(self):
        return self._fetch(self.rechatService.startWithRange)
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
    def render(self):
        self.chat.render(self.messages)
        self.rendered = True
    def scroll(self, playerTimeMs, direction="forward"):
        if(self.rendered == True):
            scroll = None
            for message in self.messages:
                if(message.absoluteTimeMs > playerTimeMs):
                    if(scroll == None):
                        self.chat.scrollTo(0)
                    else:
                        self.chat.scrollToMessage(scroll, direction=direction)
                    return
                scroll = message
            self.chat.scrollToMessage(scroll)
            xbmc.sleep(333) #let scroll animation finish
    def stop(self):
        self.chat.hide()
    def updateSettings(self, apply=False):
        self.settings.update()
        if(apply==True):
            self.applySettings()
    def toPlayerTime(self, receivedAtMs):
        return receivedAtMs - self.streamInfo.recordedAtMs

playback = PlaybackController()
playback.getStreamInfo()

lastPlayerTimeMs = 0
for i in range(100):
    if(playback.settings.updated == False):
        playback.updateSettings(apply=True)
        playback.fetchStart()
        playback.chat.prependEmpty()
    playerTimeMs = playback.getPlayerTime()
    isFetched, beforeFetchedRange, afterFetchedRange = playback.isFetchedBoundsEpsilon(playerTimeMs)
    playback.scroll(playerTimeMs, direction=("forward" if playerTimeMs > lastPlayerTimeMs else "backward") )
    lastPlayerTimeMs = playerTimeMs
    if(isFetched == False):
        if(beforeFetchedRange < 0 or afterFetchedRange > 900000):
#            d.dialog('doing after because beforeFetchedRange: [%s]\nafterFetchedRange: [%s]' %(beforeFetchedRange, afterFetchedRange))
            playback.chat.prependEmpty()
            playback.fetchAfter(playerTimeMs)
        else:
#            d.dialog('doing next because beforeFetchedRange: [%s]\nafterFetchedRange: [%s]' %(beforeFetchedRange, afterFetchedRange))
            playback.chat.prependContinue() if playback.rendered == True else playback.chat.prependEmpty()
            playback.fetchNext()
        isFetched = True #ensures rapid render
    if(isFetched == True and playback.rendered == False):
#        d.dialog('rendering')
        playback.render()
    xbmc.sleep(200)
playback.stop()
