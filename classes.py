import urllib
import json
import calendar
import datetime
import re
import functools

import xbmcaddon
import xbmc

import os
import xbmcvfs
import stuff
import dateutil.relativedelta
import dateutil.parser


CACHE_PATH = 'special://temp/reXChat/' #DONT FORGET Cache.CACHE_PATH
CACHE_PATH_TRANSLATE = xbmc.translatePath(CACHE_PATH)
ENABLE_CACHE = True
HIGHEST_DELAY = 30000
PART_DURATION = 1711650

d = stuff.Debugger()
addon = xbmcaddon.Addon()
addonname = addon.getAddonInfo('name')
addonpath = xbmc.translatePath(addon.getAddonInfo('path'))

# 2015-01-15T14:32:47.650Z
def datetimeStringToLong(string):
    dt = dateutil.parser.parse(string)
    ts = calendar.timegm(dt.utctimetuple())
    match = re.search('\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.(\d+))?Z', string)
    ms = int(match.group(2)) if match.group(2) != None else 0
    return ts * 1000 + ms

def jsonDump(path, data):
    if ENABLE_CACHE:
        with open(xbmc.translatePath(path), 'w') as outfile:
            json.dump(data, outfile)

def jsonRead(path):
    if ENABLE_CACHE:
        with open(xbmc.translatePath(path), 'r') as fileText:
            return json.load(fileText)
    else: raise Exception('Cache disabled')

def jsonRequest(url):
    response = urllib.urlopen(url)
    text = response.read()
    d.log(text)
    return json.loads(text)

# 1421332367650
def longToDatetimeString(long):
    return datetime.datetime.utcfromtimestamp(long / 1000).isoformat() + '.' + str(long)[-3:] + 'Z'

class Message():
    lineLength = 17
    linePrefix = '  '
    def __init__(self, rechatMessage, startDeltaMs):
        self.id = rechatMessage['_id']
        self.receivedAt = rechatMessage['_source']['recieved_at']
        self.receivedAtMs = datetimeStringToLong(self.receivedAt)
        self.absoluteTimeMs = self.receivedAtMs - startDeltaMs
        self.sender = rechatMessage['_source']['from']
        self.text = rechatMessage['_source']['message']
        self.isRendered = False
    def getLines(self):
        lines = list()
        consecutiveLineLength = Message.lineLength - len(Message.linePrefix)
        firstLine = self.sender + ': '
        firstLineCharsLeft = Message.lineLength - len(firstLine)
        firstLine += self.text[:firstLineCharsLeft]
        lines.append(firstLine)
        remaining = self.text[firstLineCharsLeft:]
        while len(remaining) != 0:
            line = Message.linePrefix + remaining[:consecutiveLineLength]
            lines.append(line)
            remaining = remaining[consecutiveLineLength:]
        return lines

class Cache(object):
    CACHE_PATH = None
    def __init__(self, folderName):
        self.translateCachePath = xbmc.translatePath(self.CACHE_PATH)
        self.folderName = folderName
        self.folderPath = os.path.join(self.translateCachePath, self.folderName)
    def _log(self, msg): return d.component('common.cache', msg)
    def putText(self, fileName, text):
        pass
    def putJSON(self, fileName, obj):
        path = os.path.join(self.folderPath, fileName)
        xbmcvfs.mkdirs(self.folderPath)
        self._log('putting JSON %s' %path)
        jsonDump(path, obj)
    def readJSON(self, fileName):
        path = os.path.join(self.folderPath, fileName)
        if(xbmcvfs.exists(path)):
            self._log('found JSON %s' %path)
            return jsonRead(path)
        else:
            self._log('not found JSON %s' %path)
            return None

class RechatCache(Cache):
    def __init__(self, streamInfo):
        self.streamInfo = streamInfo
        super(RechatCache, self).__init__(self.streamInfo.streamId)
    def _cacheFile(self, file):
        m = re.match('(start_)?(\d+)-(\d+)', file)
        return { 'name': file, 'start': int(m.group(2)), 'end': int(m.group(3)) }
    def _cacheFiles(self):
        def sort(a, b):
            startE = a['start'] - b['start']
            result = startE if startE != 0 else a['end'] - b['end']
            return int(result)
        dirs, files = xbmcvfs.listdir(self.folderPath)
        cacheFiles = map(self._cacheFile, files)
        sortedCacheFiles = sorted(cacheFiles, cmp=sort)
        return sortedCacheFiles
    def _findFirst(self, matches):
        return next((cacheFile for cacheFile in self._cacheFiles() if matches(cacheFile)), None)
    def _log(self, msg): return d.component('rechat.cache', msg)
    def _put(self, prefix, lastReceivedAt, response):
        fileName = '%s%s-%s' %(
            prefix,
            datetimeStringToLong(lastReceivedAt),
            datetimeStringToLong(RechatService._messages(response)[-1]['_source']['recieved_at'])
        )
        super(RechatCache, self).putJSON(fileName, response)
    def findStart(self):
        return self._findFirst(lambda cacheFile: cacheFile['name'].startswith('start_'))
    def findStrict(self, startAt):
        return self._findFirst(lambda cacheFile: startAt >= cacheFile['start'] and startAt < cacheFile['end'])
    def findLoose(self, startAt):
        return self._findFirst(lambda cacheFile: cacheFile['start'] > startAt and cacheFile['end'] > startAt)
    def putAfter(self, messagesStartAt, response):
        self._put('', messagesStartAt, response)
    def putStart(self, response):
        self._put('start_', self.streamInfo.recordedAt, response)

class RechatService(object):
    def __init__(self, streamInfo):
        self.streamInfo = streamInfo
        self.lastReceivedAt = None
        self.end = False
    def _log(self, msg): return d.component('rechat.service', msg)
    @staticmethod
    def _messages(response):
        return response["hits"]["hits"]
    def _response(self, response):
        if(response != None): #cache returns None
            rechatMessages = RechatService._messages(response)
            if(len(rechatMessages) > 0):
                self.lastReceivedAt = rechatMessages[-1]['_source']['recieved_at']
                self.end = False
                return rechatMessages
        self.end = True
        return []
    def _searchAfter(self, after):
        url = self._log('http://search.rechat.org/videos/%s?after=%s' %(self.streamInfo.streamId, urllib.quote_plus(after)))
        return jsonRequest(url)
    def _searchStart(self):
        url = self._log('http://search.rechat.org/videos/%s' %self.streamInfo.streamId)
        return jsonRequest(url)
    def after(self, after):
        return self._response(self._searchAfter(after))
    def afterMs(self, afterMs):
        return self.after(longToDatetimeString(afterMs))
    def hasMore(self):
        return not self.end
    def next(self):
        if (self.lastReceivedAt == None):
            response = self._searchStart()
        else:
            response = self._searchAfter(self.lastReceivedAt)
        rechatMessages = self._response(response)
        return rechatMessages

class CachedRechatService(RechatService):
    def __init__(self, streamInfo):
        super(CachedRechatService, self).__init__(streamInfo)
        self.cache = RechatCache(streamInfo)
    def _log(self, msg): return d.component('rechat.cService', msg)
    def _search(self, cacheCheck, rechatCall, cachePut, fallbackCacheCheck):
        cacheFileName = cacheCheck()
        response = self.cache.readJSON(cacheFileName['name']) if cacheFileName else None
        if(response == None):
            response = rechatCall()
            if(len(RechatService._messages(response)) > 0):
                cachePut(response)
            else:
                self._log('trying fallback check in cache in case logs were removed')
                cacheFileName = fallbackCacheCheck()
                if(cacheFileName != None):
                    response = self.cache.readJSON(cacheFileName['name'])
                else:
                    self._log('fallback didnt find anything')
                    response = None
        return response
    def _searchAfter(self, after):
        afterMs = datetimeStringToLong(after)
        cacheCheck = functools.partial(self.cache.findStrict, afterMs)
        rechatCall = functools.partial(super(CachedRechatService, self)._searchAfter, after)
        cachePut = functools.partial(self.cache.putAfter, after)
        fallbackCacheCheck = functools.partial(self.cache.findLoose, afterMs)
        return self._search(cacheCheck, rechatCall, cachePut, fallbackCacheCheck)
    def _searchStart(self):
        cacheCheck = self.cache.findStart
        rechatService = super(CachedRechatService, self)._searchStart
        cachePut = self.cache.putStart
        fallbackCacheCheck = functools.partial(self.cache.findLoose, 0)
        return self._search(cacheCheck, rechatService, cachePut, fallbackCacheCheck)

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

# d.dialog(datetimeStringToLong('2015-01-15T14:32:47Z'))
# d.dialog(datetimeStringToLong('2015-01-15T14:32:47.650Z'))
# tVideo = TwitchVideo('a611375915', '02')
# d.dialog(tVideo.videoId)
# d.dialog(tVideo.streamId)
# d.dialog(tVideo.recordedAt)
# d.dialog(len(tVideo.messages))

Cache.CACHE_PATH = CACHE_PATH
