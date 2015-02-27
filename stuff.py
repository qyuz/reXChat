import xbmc, xbmcgui, os, xbmcaddon, urllib, json

addon = xbmcaddon.Addon()
addonname = addon.getAddonInfo('name')
ACTION_PREVIOUS_MENU = 10


class Debugger():
    counter = 0
    def component(self, name, msg):
        xbmc.log("[reXChat]%s[%s]: %s" %(' '*(15-len(name)), name, msg))
        return msg
    def log(self, text):
        xbmc.log(str(self.counter) + ' [reThat]: ' + str(text))
        self.counter += 1
    def dialog(self, message):
        dialog = xbmcgui.Dialog()
        dialog.ok("Debugger", str(message))

d = Debugger()

class Utils():
    def readFile(self):
        file = open('C:\Documents and Settings\Ljoha\Application Data\XBMC\cache\changelog.txt')
        text = file.read()
        return text

class XBMCPlayer( xbmc.Player):

    def __init__( self, *args ):
        pass

    def onPlayBackStarted( self ):
        # Will be called when xbmc starts playing a file
        d.log( "LED Status: Playback Started, LED ON" )

    def onPlayBackEnded( self ):
        # Will be called when xbmc stops playing a file
        d.log( "LED Status: Playback Stopped, LED OFF" )

    def onPlayBackStopped( self ):
        # Will be called when user stops xbmc playing a file
        d.log( "LED Status: Playback Stopped, LED OFF" )

    def onPlayBackPaused(self):
        d.log('paused')

class GUI(xbmcgui.WindowXMLDialog):
    focus = 0
    currentLog = 0
    buttons = list()
    buttonsDict = {}

    def __init__(self, *args, **kwargs):
        # xbmcgui.WindowXMLDialog.__init__(self)
#        self.window = xbmcgui.Window(kwargs.get("windowId"))
        pass


    def tPrintChat(self):
        control = self.window.getControl(1331)
        for (i, messafgeHolder) in enumerate(self.hits):
            pass
            # log(messageHolder['_id'])
            # log(messageHolder['_source']['message'])
            # control.addItem(xbmcgui.ListItem(label2=messageHolder['_source']['message']))

    def loadLogs(self):
        response = urllib.urlopen('http://search.rechat.org/videos/v3800416')
        text = response.read()
        videoLogs = json.loads(text)
        self.hits = videoLogs['hits']['hits']
        d.dialog('loaded logs')

    def getLog(self, i):
        currLog = self.hits[self.currentLog]
        self.currentLog += 1
        return currLog

    def tButton(self):
        self.appendButton("UP")
        self.appendButton("DOWN")
        self.appendButton("ADD")
        self.appendButton("SIZE")
        self.appendButton("TIME")
        self.appendButton("PLAYER")

    def appendButton(self, name):
        x, y, width, height, step = 350,  450, 80, 30, 5
        self.buttons.append(xbmcgui.ControlButton(x, y + (len(self.buttons) - 1) * (height + step), width, height, name))
        self.buttonsDict[name] = self.buttons[len(self.buttons) - 1]
        self.addControl(self.buttons[len(self.buttons) - 1])
        self.setFocus(self.buttons[len(self.buttons) - 1])
        if(len(self.buttons) > 1):
            self.buttons[len(self.buttons) - 2].controlDown(self.buttons[len(self.buttons) - 1])
            self.buttons[len(self.buttons) - 1].controlUp(self.buttons[len(self.buttons) - 2])

    def onInit(self):
        self.window = xbmcgui.Window(xbmcgui.getCurrentWindowDialogId())
        self.window.setProperty('windowLabel', 'IrcChat')

        control = self.window.getControl(1331)
        message = {0: 'this is list item', 1: 'asdf'}
        control.addItem(xbmcgui.ListItem(label=message[0]))
        self.loadLogs()
        # self.tPrintChat()
        self.tButton()
        return

    def get_keyboard_input(self, label):
        pass

    def onAction(self, action):
        if action == ACTION_PREVIOUS_MENU:
            self.close()
        if action == 20:
            d.dialog('step forward')

    def onClick(self, id):
        control = self.window.getControl(1331)
        d.log('onClick')
        if id == self.buttonsDict["UP"].getId():
            self.focus += 1
            d.log('up ' + str(self.focus))
            control.selectItem(self.focus)
            xbmc.executebuiltin("Control.move(1331, %s)" %control.size())
        if id == self.buttonsDict["DOWN"].getId():
            self.focus -= 1
            d.log('down ' + str(self.focus))
            control.selectItem(self.focus)
            xbmc.executebuiltin("Control.move(1331, %s)"  %control.size())
        if id == self.buttonsDict["ADD"].getId():
            messageHolder = self.getLog(self.currentLog)
            control.addItem(xbmcgui.ListItem(label=messageHolder['_source']['message']))
            self.focus += 1
            d.log('up ' + str(self.focus))
            control.selectItem(self.focus)
            xbmc.executebuiltin("Control.move(1331, %s)" %control.size())
            # control.addItem(xbmcgui.ListItem(label='e\r\nf\r\ng\r\nh'))
        if id == self.buttonsDict["SIZE"].getId():
            d.dialog(control.size())
        if id == self.buttonsDict["TIME"].getId():
            d.dialog(xbmc.Player().getTime())
        if id == self.buttonsDict["PLAYER"].getId():
            if xbmc.getCondVisibility("Window.IsVisible(fullscreenvideo)") == False:
                xbmc.executebuiltin("ActivateWindow(fullscreenvideo)")
            else:
                xbmc.executebuiltin("ActivateWindow(videoosd)")


    # credit - http://stackoverflow.com/a/15274929
    def terminate_thread(self, thread):
        """Terminates a python thread from another thread.

        :param thread: a threading.Thread instance
        """
        pass

#window = GUI('script-reThat-main.xml', xbmc.translatePath(addon.getAddonInfo('path')))
#window.doModal()

class OverlayText(object):
    def __init__(self):
        self.showing = False
        self.window = xbmcgui.Window(12005)
        viewport_w, viewport_h = self._get_skin_resolution()
        font_max = 'font13'
        font_min = 'font10'
        origin_x = int(float(viewport_w)/1.3913)
        origin_y = int(float(viewport_h)/8.0)
        window_w = int(float(viewport_w)/3.7647)
        window_h = int(float(viewport_h)/2.5714)
        acelogo_w = int(float(window_w)/8.5)
        acelogo_h = int(float(window_w)/11.0)
        text_lat = int(float(window_w)/15)
        text_w = int(float(window_w)/1.7)
        text_h = int(float(window_h)/14)
        fst_setting = int(float(window_h)/3.5)
        fst_stat_setting = int(float(window_h)/1.4)

        #main window
        clist = xbmcgui.ControlList(1, 1, 1, 1)
        clist.setAnimations([('focus', 'effect=zoom end=90,247,220,56 time=0',)])
        self._background = xbmcgui.ControlImage(origin_x, origin_y, window_w, window_h, os.path.join(addonpath,"resources","art","lateral-fundo.png"))
        self._acestreamlogo = xbmcgui.ControlImage(origin_x + int(float(window_w)/11.3), origin_y + int(float(window_h)/14), acelogo_w, acelogo_h, os.path.join(addonpath,"resources","art","acestreamlogo.png"))
        self._supseparator = xbmcgui.ControlImage(origin_x, origin_y + int(float(viewport_h)/12.176), window_w-10, 1, os.path.join(addonpath,"resources","art","lateral-separador.png"))
        self._botseparator = xbmcgui.ControlImage(origin_x, origin_y + window_h - 30, window_w-10, 1, os.path.join(addonpath,"resources","art","lateral-separador.png"))
        self._title = xbmcgui.ControlLabel(origin_x+int(float(window_w)/3.4), origin_y + text_h, window_w - 140, text_h, str(50000), font=font_max, textColor='0xFFEB9E17')
        self._total_stats_label = xbmcgui.ControlLabel(origin_x+int(float(window_h)/1.72), origin_y + int(float(window_h)/1.6), int(float(window_w)/1.7), 20, str(50005), font=font_min, textColor='0xFFEB9E17')
        #labels
        self._action = xbmcgui.ControlLabel(origin_x + text_lat, origin_y + fst_setting, int(float(text_w)*1.6), text_h, str(50001) + '  N/A', font=font_min)
        self._download = xbmcgui.ControlLabel(origin_x + text_lat, origin_y + fst_setting + text_h, int(float(text_w)*1.6), text_h, str(50002) + '  N/A', font=font_min)
        self._upload = xbmcgui.ControlLabel(origin_x + text_lat, origin_y + fst_setting + 2*text_h, text_w, text_h, str(50003) + '  N/A', font=font_min)
        self._seeds = xbmcgui.ControlLabel(origin_x + text_lat, origin_y + fst_setting + 3*text_h, text_w, text_h, str(50004) + '  N/A', font=font_min)
        self._total_download = xbmcgui.ControlLabel(origin_x + text_lat, origin_y + fst_stat_setting, text_w, text_h, str(50006) + '  N/A', font=font_min)
        self._total_upload = xbmcgui.ControlLabel(origin_x + text_lat, origin_y + fst_stat_setting + text_h, text_w, text_h, str(50007) + '  N/A', font=font_min)
        self._percent_value = xbmcgui.ControlLabel(origin_x+int(float(window_h)/1.05), origin_y + fst_setting, text_w, text_h,'N/A', font=font_min)

    def show(self):
        self.showing=True
        self.window.addControl(self._background)
        self.window.addControl(self._acestreamlogo)
        self.window.addControl(self._supseparator)
        self.window.addControl(self._botseparator)
        self.window.addControl(self._title)
        self.window.addControl(self._action)
        self.window.addControl(self._download)
        self.window.addControl(self._upload)
        self.window.addControl(self._seeds)
        self.window.addControl(self._total_stats_label)
        self.window.addControl(self._total_download)
        self.window.addControl(self._total_upload)
        self.window.addControl(self._percent_value)


    def hide(self):
        self.showing=False
        self.window.removeControl(self._total_download)
        self.window.removeControl(self._total_upload)
        self.window.removeControl(self._percent_value)
        self.window.removeControl(self._title)
        self.window.removeControl(self._action)
        self.window.removeControl(self._download)
        self.window.removeControl(self._upload)
        self.window.removeControl(self._seeds)
        self.window.removeControl(self._total_stats_label)
        self.window.removeControl(self._acestreamlogo)
        self.window.removeControl(self._supseparator)
        self.window.removeControl(self._botseparator)
        self.window.removeControl(self._background)

    def set_information(self,engine_data):
        if self.showing == True:
            self._action.setLabel(str(50001) + '  ' + engine_data["action"])
            self._percent_value.setLabel(engine_data["percent"])
            self._download.setLabel(str(50002)+ '  ' + engine_data["download"])
            self._upload.setLabel(str(50003) + '  ' + engine_data["upload"])
            self._seeds.setLabel(str(50004) + '  ' + engine_data["seeds"])
            self._total_download.setLabel(str(50006) + '  ' + engine_data["total_download"])
            self._total_upload.setLabel(str(50007) + '  ' + engine_data["total_upload"])
        else: pass

    def _close(self):
        if self.showing:
            self.hide()
        else:
            pass
        try:
            self.window.clearProperties()
            print("OverlayText window closed")
        except: pass

    #Taken from xbmctorrent
    def _get_skin_resolution(self):
        import xml.etree.ElementTree as ET
        skin_path = xbmc.translatePath("special://skin/")
        tree = ET.parse(os.path.join(skin_path, "addon.xml"))
        try: res = tree.findall("./res")[0]
        except: res = tree.findall("./extension/res")[0]
        return int(res.attrib["width"]), int(res.attrib["height"])
