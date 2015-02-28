import common, functools, re, urllib, xbmcvfs
from common import datetimeStringToLong, jsonRequest, longToDatetimeString

d = common.Debugger()

class RechatCache(common.Cache):
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
