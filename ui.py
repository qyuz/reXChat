import os, xbmc, xbmcaddon, xbmcgui

addon = xbmcaddon.Addon()
addonPath = xbmc.translatePath(addon.getAddonInfo('path'))
mediaPath = os.path.join(addonPath, 'resources', 'skins', 'Default', 'media')

class OverlayChat(object):
    def __init__(self):
        self.showing = True
        self.fullScreenVideo = xbmcgui.Window(12005)
        chatBackground = os.path.join(mediaPath, 'ChatBackground.png')
        self.background = xbmcgui.ControlImage(-110, 0, 418, 564, chatBackground, aspectRatio=0)
        # w*22 font12 width 320, itemTextXOffset -2
        self.chat = xbmcgui.ControlList(0, 0, 320, 600, 'font12', 'FFFFFFFF', 'IrcChat/ChatArrowFO.png', 'pstvButtonFocus.png', 'FFFFFFFF', 0, 0, -2, 0, 20, 0, 0)
        self.fullScreenVideo.addControl(self.background)
        self.fullScreenVideo.addControl(self.chat)
        self.id = self.chat.getId()
    def addLine(self, line):
        self.chat.addItem(line)
    def show(self):
        self.showing = True
    def hide(self):
        self.showing = False
        self.fullScreenVideo.removeControl(self.background)
        self.fullScreenVideo.removeControl(self.chat)
    def scrollTo(self, index):
        index = int(index)
        self.chat.selectItem(index)
    def resizeBackground(self, x, y, width, height):
        self.fullScreenVideo.removeControl(self.background)
        self.background = xbmcgui.ControlImage(x, y, width, height, xbmc.translatePath(classes.CACHE_PATH + 'ChatBackground.png'))
        self.fullScreenVideo.addControl(self.background)

class ChatRenderer(OverlayChat):
    def __init__(self):
        super(ChatRenderer, self).__init__()
        self.messageIndex = {}
    def addMessage(self, message):
        for line in message.getLines():
            self.addLine(line)
        self.messageIndex[message.id] = self.chat.size() - 1
    def setMessages(self, messages, focus=None):
        self.messageIndex = {}
        self.chat.reset()
        for message in messages:
            self.addMessage(message)
    def scrollToMessage(self, message):
        self.scrollToMessageId(message.id)
    def scrollToMessageId(self, messageId):
        self.scrollTo(self.messageIndex[messageId])
