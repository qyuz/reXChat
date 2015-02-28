import common, rechat, twitch, xbmc, xbmcvfs
from common import Cache, Debugger


Cache.CACHE_PATH = 'special://temp/reXChat/'
d = Debugger()
streams = [
    'v3800416',
]

def download():
    twitchAPI = twitch.CachedAPI()
    for streamId in streams:
        streamInfo = twitchAPI.getStreamInfo(streamId = streamId)
        rechatService = rechat.CachedService(streamInfo)
        while(rechatService.hasMore()):
            rechatService.next()
        d.dialog('DONE WITH %s' %streamId)
        rechatService.afterMs(1424210689268)
        d.dialog(rechatService.hasMore())

download()
d.dialog('DONE')