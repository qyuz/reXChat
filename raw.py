import xbmc, xbmcgui

def msg(txt):
    dialog = xbmcgui.Dialog()
    dialog.ok("Debugger", str(txt))

msg('started')

while(True):
    xbmc.log('yo')
    xbmc.sleep(1000)
    xbmc.log('yoo')

msg('finished')
