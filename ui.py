import os, xbmc, xbmcaddon, xbmcgui

addon = xbmcaddon.Addon()
addonPath = xbmc.translatePath(addon.getAddonInfo('path'))
mediaPath = os.path.join(addonPath, 'resources', 'skins', 'Default', 'media')

class OverlayChat(object):
    def __init__(self, parentWindow=12005,
                 backgroundX=-110, backgroundY=0, backgroundWidth=418, backgroundHeight=608,
                 chatX=0, chatY=0, chatWidth=320, chatHeight=600, lineHeight=20, fontSize='font12'):
        self.showing = True
        self.fullScreenVideo = xbmcgui.Window(parentWindow)
        chatBackground = os.path.join(mediaPath, 'ChatBackground.png')
        self.background = xbmcgui.ControlImage(backgroundX, backgroundY, backgroundWidth, backgroundHeight, chatBackground, aspectRatio=0)
        self.chat = xbmcgui.ControlList(chatX, chatY, chatWidth, chatHeight, fontSize, 'FFFFFFFF', 'IrcChat/ChatArrowFO.png', 'pstvButtonFocus.png', 'FFFFFFFF', 0, 0, 0, 0, lineHeight, 0, 0)
        self.setChatRowCount(chatHeight, lineHeight)
        self.fullScreenVideo.addControl(self.background)
        self.fullScreenVideo.addControl(self.chat)
        self.id = self.chat.getId()
    def addLine(self, line):
        self.chat.addItem(line)
    def addLines(self, lines):
        for line in lines:
            self.addLine(line)
    def show(self):
        self.showing = True
    def hide(self):
        self.showing = False
        self.fullScreenVideo.removeControl(self.background)
        self.fullScreenVideo.removeControl(self.chat)
    def scrollTo(self, index, direction="forward"):
        if(direction == "forward"):
            index = index
        else:
            index = index - (self.chatRowCount - 1 - 2) #ControlList is fishy
        self.chat.selectItem(index)
    def setChatRowCount(self, height, rowHeight):
        self.chatRowCount = int(height / rowHeight)
    def resizeBackground(self, x, y, width, height):
        self.background.setPosition(x, y)
        self.background.setWidth(width)
        self.background.setHeight(height)
    def resizeChat(self, x, y, width, height, rowHeight):
        self.chat.setPosition(x, y)
        self.chat.setWidth(width)
        self.chat.setHeight(height)
        self.chat.setItemHeight(rowHeight)
        self.setChatRowCount(height, rowHeight)

class ChatRenderer(OverlayChat):
    def __init__(self):
        super(ChatRenderer, self).__init__()
        self.messageIndex = {}
        self.prependLines = []
    def addMessage(self, message):
        self.addLines(message.getLines())
        self.messageIndex[message.id] = self.chat.size() - 1
    def addMessages(self, messages, focus=None):
        for message in messages:
            self.addMessage(message)
    def clear(self):
        self.messageIndex = {}
        self.chat.reset()
    def prependEmpty(self):
        self.prependLines = [''] * self.chatRowCount
    def prependContinue(self):
        self.prependLines = [self.chat.getListItem(self.chat.size() - i).getLabel() for i in range(1, self.chatRowCount + 1)]
        self.prependLines.reverse()
    def render(self, messages):
        self.clear()
        self.addLines(self.prependLines)
        self.addMessages(messages)
    def setMessages(self, messages, focus=None):
        self.clear()
        for message in messages:
            self.addMessage(message)
    def scrollToMessage(self, message, direction="forward"):
        self.scrollToMessageId(message.id, direction=direction)
    def scrollToMessageId(self, messageId, direction="forward"):
        self.scrollTo(self.messageIndex[messageId] - 2, direction=direction) #ControlList is fishy
