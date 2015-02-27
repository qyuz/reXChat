import xbmcaddon
import xbmcgui
import xbmc
import xbmcvfs

import stuff
import classes

import  time

d = stuff.Debugger()
# d.dialog('script started')
addon = xbmcaddon.Addon()
# addon.openSettings()
addonname = addon.getAddonInfo('name')
addonpath = xbmc.translatePath(addon.getAddonInfo('path'))

ACTION_PREVIOUS_MENU = 10

class OverlayChat():
    def __init__(self):
        self.showing = False
        self.window = xbmcgui.Window(12005)

        #main window
        chatBackground = xbmc.translatePath(classes.CACHE_PATH + 'ChatBackground.png')
        # chatBackgroundResized = xbmc.translatePath(twitchvideo.cachePath + 'ChatBackgroundResized.jpeg')
        # im = Image.open(chatBackground)
        # im.thumbnail((320, 600), Image.ANTIALIAS)
        # im.save(chatBackgroundResized, "JPEG")
        self.background = xbmcgui.ControlImage(-110, 0, 418, 564, chatBackground, aspectRatio=0)
        # w*22 font12 width 320, itemTextXOffset -2
        self.clist = xbmcgui.ControlList(0, 0, 320, 600, 'font12', 'FFFFFFFF', 'IrcChat/ChatArrowFO.png', 'pstvButtonFocus.png', 'FFFFFFFF', 0, 0, -2, 0, 20, 0, 0)
        self.window.addControl(self.background)
        self.window.addControl(self.clist)
        self.id = self.clist.getId()
        # listItem = xbmcgui.ListItem('yoyoyo', 'asdfasdf')
        # listItem1 = xbmcgui.ListItem('yoyoyo', 'asdfasdf2')
        # listItem2 = xbmcgui.ListItem('yoyoyo', 'asdfasdf3')
        # listItem3 = xbmcgui.ListItem('yoyoyo', 'asdfasdf4')
        # self.clist.addItem('uau')
        # self.clist.addItem(listItem1)
        # self.clist.addItem(listItem2)
        # self.clist.addItem(listItem3)
        # self.clist.selectItem(0)
        # self.clist.selectItem(1)
        # self.window.setFocus(self.clist)
        # listItem.select(True)
        # d.dialog(self.clist.size())
        # self.clist.setAnimations([('focus', 'effect=zoom end=90,247,220,56 time=0',)])

    def addLine(self, line):
        self.clist.addItem(line)
        xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Input.Down", "id": %s }' %(self.id))

    def show(self):
        self.showing=True

    def hide(self):
        self.showing=False
        self.window.removeControl(self.background)
        self.window.removeControl(self.clist)

    def scrollTo(self, index):
        index = int(index)
        self.clist.selectItem(index)
#        c_size = self.clist.size()
#        xbmc.executebuiltin("Control.move(" + str(self.clist.getId()) + ", %s)" %'1')
#        xbmc.executebuiltin("Control.move(" + str(self.clist.getId()) + ", %s)" %index)
#        xbmc.executebuiltin("Control.move(1331, %s)" %c_size)

    def resizeBackground(self, x, y, width, height):
        self.window.removeControl(self.background)
        self.background = xbmcgui.ControlImage(x, y, width, height, xbmc.translatePath(classes.CACHE_PATH + 'ChatBackground.png'))
        self.window.addControl(self.background)

    def _close(self):
        if self.showing:
            self.hide()
        else:
            pass
        try:
            self.window.clearProperties()
            print("OverlayText window closed")
        except: pass


class PlaybackController(xbmc.Monitor):
    def __init__(self):
        self.settings = Settings()
        classes.Message.lineLength = self.settings.characters
        self.chat = ChatRenderer(self.settings)
    def kill(self):
        self.chat.close()
    def now(self):
        self.chat.scroll(xbmc.Player().getTime() * 1000)
    def onSettingsChanged(self):
        self.settings.update()
        # lat123.resizeBackground(settings.backgroundX, settings.backgroundY, settings.backgroundWidth, settings.backgroundHeight)

class ChatRenderer():
    def __init__(self, settings):
        self.messageIndex = {}
        self.video = twitch.ArchiveVideo(None, 1, streamId='v3725446')
        self.chat = OverlayChat()
        self.chat.show()
        self.delay = settings.delay
#        self.chat.populate() #1
#        self.chat.clist.reset()
    def addMessage(self, message):
        for line in message.getLines():
            self.chat.addLine(line)
            message.isRendered = True
        self.messageIndex[message.id] = self.chat.clist.size() - 1
    def close(self):
        self.chat._close()
    def populate(self):
        for message in self.video.messages:
            self.addMessage(message)
    def scroll(self, playerTime):
        scroll = None
        delayedTime = playerTime + self.delay
        index = self.chat.clist.size()
        id = self.chat.clist.getId()
        for message in self.video.messages:
            if message.absoluteTimeMs < delayedTime and message.isRendered == False:
                d.dialog('before')
                self.addMessage(message) #1
                d.dialog('after')
#                d.dialog('added')
#                xbmc.sleep(50)
                pass #1
            elif message.absoluteTimeMs > delayedTime:
                if scroll:
                    self.chat.scrollTo(self.messageIndex[scroll.id])
#                    d.dialog('scroll')
#                    xbmc.sleep(2000)
                return
#            else: # Wonders happen
#                self.addMessage(message) #1
#                self.chat.scrollTo(self.messageIndex[message.id])
#                return
            scroll = message

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


def drawUI():
    playbackController = PlaybackController()
    #try:
    count = 0
    while(count < 25):
        xbmc.sleep(500)
        playbackController.now()
        count += 1
    #except: d.dialog('exception')
    playbackController.kill()

def rechatServiceTest():
    twitchAPI = classes.CachedTwitchAPI()
#    streamInfo = twitchAPI.getStreamInfo(videoId='a611375915')
#    d.dialog(streamInfo.streamId)
#    d.dialog(streamInfo.recordedAt)
#    d.dialog(streamInfo.recordedAtMs)
#    streamInfo = twitchAPI.getStreamInfo(streamId='v3832313')
#    streamInfo = twitchAPI.getStreamInfo(streamId='v3676602') # checks findLoose on start
    streamInfo = twitchAPI.getStreamInfo(streamId='v3800416')
#    d.dialog(streamInfo.streamId)
#    d.dialog(streamInfo.recordedAt)
#    d.dialog(streamInfo.recordedAtMs)
#    rechatService = classes.RechatService('v3800416', 1424183641000)
#    rechatService = classes.RechatService(streamInfo)
#    rMessages = rechatService.next()
#    d.dialog(rMessages[-1])
#    d.dialog(rechatService.next()[-1])
#    d.dialog(rechatService.afterMs(1424183641000)[-1])
#    d.dialog(rechatService.next()[-1])
    cachedRechatService = classes.CachedRechatService(streamInfo)
    cRMessages = cachedRechatService.next()
    d.dialog(cRMessages[-1])
    cRMessages = cachedRechatService.next()
    d.dialog(cRMessages[-1])
    cRMessages = cachedRechatService.afterMs(1424183641000)
    d.dialog(cRMessages[-1])

#drawUI()
rechatServiceTest()


