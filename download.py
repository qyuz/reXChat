import xbmc, xbmcvfs, stuff, classes


d = stuff.Debugger()
streams = [
    'v3800416',
]

def oldDownload():
    for streamId in streams:
        twitch.CACHE_PATH = 'special://temp/reXChat/' + streamId + '/'
        xbmcvfs.mkdir(xbmc.translatePath(twitch.CACHE_PATH))
        cPart = 1
        try:
            while(True):
                tVideo = twitch.ArchiveVideo(None, cPart, streamId=streamId)
                cPart += 1
        except:
            d.dialog('finished ' + streamId + ' on ' + str(cPart) + ' part')


def download():
    twitchAPI = classes.TwitchAPI()
    for streamId in streams:
        streamInfo = twitchAPI.getStreamInfo(streamId = streamId)
        rechatService = classes.CachedRechatService(streamInfo)
        while(rechatService.hasMore()):
            rechatService.next()
        d.dialog('DONE WITH %s' %streamId)
        rechatService.afterMs(1424210689268)
        d.dialog(rechatService.hasMore())

download()
d.dialog('DONE')