import common
from common import Cache, datetimeStringToLong, Debugger, jsonRequest

d = Debugger()

class StreamInfo():
    def __init__(self, streamInfoJson):
        self.streamId = streamInfoJson['_id']
        self.recordedAt = streamInfoJson['recorded_at']
        self.recordedAtMs = datetimeStringToLong(self.recordedAt)

class TwitchAPI(object):
    def __init__(self):
        pass
    def _log(self, msg):return d.component('twitch.api', msg)
    def getStreamInfo(self, streamId=None, videoId=None):
        videoInfo = None
        if streamId == None:
            videoInfo = self.videoInfo(videoId)
            streamId = 'v%s' %videoInfo['redirect_api_id']
        streamInfoJson = self.streamInfo(streamId)
        streamInfo = StreamInfo(streamInfoJson)
        return streamInfo
    def streamInfo(self, streamId): #v3691491
        url = self._log('https://api.twitch.tv/kraken/videos/%s' %streamId)
        return jsonRequest(url)
    def videoInfo(self, videoId): #a611375915
        url = self._log('http://api.twitch.tv/api/videos/%s' %videoId)
        return jsonRequest(url)

class CachedTwitchAPI(TwitchAPI):
    def __init__(self):
        self.cache = Cache('twitch')
    def _log(self, msg): return d.component('twitch.cApi', msg)
    def _getInfo(self, id, superGetInfo):
        json = self.cache.readJSON(id)
        if(json != None):
            return json
        else:
            response = superGetInfo(id)
            self.cache.putJSON(id, response)
            return response
    def streamInfo(self, streamId):
        return self._getInfo(streamId, super(CachedTwitchAPI, self).streamInfo)
    def videoInfo(self, videoId):
        return self._getInfo(streamId, supert(CachedTwitchAPI, self).videoInfo)
