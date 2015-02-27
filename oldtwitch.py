import urllib
import json
import calendar
import datetime
import re

import xbmcaddon
import xbmc

import os
import xbmcvfs
import stuff
import dateutil.relativedelta
import dateutil.parser


CACHE_PATH = 'special://temp/reXChat/'
CACHE_PATH_TRANSLATE = xbmc.translatePath(CACHE_PATH)
ENABLE_CACHE = True
HIGHEST_DELAY = 30000
PART_DURATION = 1711650

d = stuff.Debugger()
xbmcvfs.mkdir(xbmc.translatePath(CACHE_PATH))
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
    return json.loads(text)

# v3691491
def loadTwitchStreamInfo(streamId):
    filePath = CACHE_PATH + streamId + '_stream.json'
    try: streamInfo = jsonRead(filePath)
    except:
        streamInfo = jsonRequest('https://api.twitch.tv/kraken/videos/' + streamId)
        jsonDump(filePath, streamInfo)
    return streamInfo

# 1421332367650
def longToDatetimeString(long):
    return datetime.datetime.utcfromtimestamp(long / 1000).isoformat() + '.' + str(long)[-3:] + 'Z'

class ArchiveVideo():
    def __init__(self, archiveId, part, streamId=None):
        if (archiveId != None):
            self.archiveId = str(archiveId)
            self.videoInfo = self.loadArchiveVideoInfo()
            self.streamId = 'v' + str(self.videoInfo["redirect_api_id"])
        else:
            self.streamId = streamId
        self.part = int(part)
        self.streamInfo = loadTwitchStreamInfo(self.streamId)
        self.recordedAt = self.streamInfo["recorded_at"]
        self.recordedAtMs = datetimeStringToLong(self.recordedAt)
        self.log = Log(self.streamId, self.part, self.recordedAtMs)
        self.messages = self.buildMessages()
    def buildMessages(self):
        return list(Message(rm, self.log.partStartMs) for rm in self.log.messages)
    def getMessages(self, absoluteTimeMs):
        return self.messages, self.log.partStartMs, self.log.partEndMs
    # a611375915
    def loadArchiveVideoInfo(self):
        filePath = CACHE_PATH + self.archiveId + '_video.json'
        try: archiveVideoInfo = jsonRead(filePath)
        except:
            archiveVideoInfo = jsonRequest('http://api.twitch.tv/api/videos/' + self.archiveId)
            jsonDump(filePath, archiveVideoInfo)
        return archiveVideoInfo

class CachedRechatService():
    def __init__(self, streamId, startMs):
        self.streamId = streamId
        self.startMs = startMs
        self.lastReceivedAt = None
    def _jsonDump(self, lastReceivedAt, rechatMessages):
        if ENABLE_CACHE:
            streamFolder = os.path.join(CACHE_PATH_TRANSLATE, self.streamId)
            if xbmcvfs.exists(streamFolder) == False: xbmcvfs.mkdirs(streamFolder)
            fileName = '%s%s-%s' %(
                'start_' if lastReceivedAt == None else '',
                datetimeStringToLong(lastReceivedAt) if lastReceivedAt else self.startMs,
                datetimeStringToLong(rechatMessages[-1]['_source']['recieved_at'])
            )
            path = os.path.join(streamFolder, fileName)
            d.log('Cached response to %s' %path)
            with open(path, 'w') as outfile:
                json.dump(rechatMessages, outfile)
    def _jsonRead(path):
        with open(xbmc.translatePath(path), 'r') as fileText:
            return json.load(fileText)
    def _cachedSearch(self):
        if ENABLE_CACHE:
            streamFolder = os.path.join(CACHE_PATH_TRANSLATE, self.streamId)
            dirs, files = xbmcvfs.listdir(streamFolder)
            startFile = None
            for file in files:
                if "start" in file:
                    startFile = file
                    break;
            d.log("%s start for %s stream %s" %(
                "Found" if startFile else "Not found",
                self.streamId,
                "[%s]" %startFile if startFile else ""
            ))
            return startFile
    def _cachedSearchAfter(self, afterMs):
        if ENABLE_CACHE:
            streamFolder = os.path.join(CACHE_PATH_TRANSLATE, self.streamId)
            dirs, files = xbmcvfs.listdir(streamFolder)
            foundFile = None
            for file in files:
                m = re.search('([^_]+_)?(\d+)-(\d+)', file)
                start = int(m.group(2))
                end = int(m.group(3))
                if afterMs >= start and afterMs <= end:
                    foundFile = file
                    break;
            d.log("%s after %s for %s stream %s" %(
                "Found" if foundFile else "Not found",
                afterMs,
                self.streamId,
                "[%s]" %foundFile if foundFile else ""
                ))
            return foundFile
    def _messages(self, response):
        responseMessages = response["hits"]["hits"]
        return responseMessages
    def _response(self, response):
        rechatMessages = self._messages(response)
        end = True if (len(rechatMessages) == 0) else False
        self.lastReceivedAt = rechatMessages[-1]['_source']['recieved_at']
        return rechatMessages, end
    def _search(self):
        self._cachedSearch()
        url = 'http://search.rechat.org/videos/%s' %self.streamId
        d.log('search url: %s' %url)
        return jsonRequest(url)
    def _searchAfter(self, after):
        self._cachedSearchAfter(datetimeStringToLong(after))
        url = 'http://search.rechat.org/videos/%s?after=%s' %(self.streamId, urllib.quote_plus(after))
        d.log('searchAfter url: %s' %url)
        return jsonRequest(url)
    def after(self, timeMs):
        response = self._searchAfter(longToDatetimeString(timeMs))
        rechatMessages, end = self._response(response)
        return rechatMessages, end
    def next(self):
        lastReceivedAt = self.lastReceivedAt
        if (self.lastReceivedAt == None):
            response = self._search()
        else:
            response = self._searchAfter(self.lastReceivedAt)
        rechatMessages, end = self._response(response)
        self._jsonDump(lastReceivedAt, rechatMessages)
        return rechatMessages, end

class RechatService():
    def __init__(self, streamId): #pass stream object instead
        self.streamId = streamId
        self.lastReceivedAt = None
    def _log(self, msg):
        d.log('[rechat.service] %s' %msg)
    def _messages(self, response):
        responseMessages = response["hits"]["hits"]
        return responseMessages
    def _response(self, response):
        rechatMessages = self._messages(response)
        self.lastReceivedAt = rechatMessages[-1]['_source']['recieved_at']
        return rechatMessages
    def _searchAfter(self, after):
        url = 'http://search.rechat.org/videos/%s?after=%s' %(self.streamId, urllib.quote_plus(after))
        self._log(url)
        return jsonRequest(url)
    def _searchStart(self):
        url = 'http://search.rechat.org/videos/%s' %self.streamId
        self._log(url)
        return jsonRequest(url)
    def after(self, timeMs):
        response = self._searchAfter(longToDatetimeString(timeMs))
        rechatMessages = self._response(response)
        return rechatMessages
    def next(self):
        lastReceivedAt = self.lastReceivedAt
        if (self.lastReceivedAt == None):
            response = self._searchStart()
        else:
            response = self._searchAfter(self.lastReceivedAt)
        rechatMessages = self._response(response)
        return rechatMessages

class TwitchAPI():
    def __init__(self):
        pass
    def _log(self, msg):
        d.component('twitch.api', msg)
    def getStreamInfo(self, streamId=None, videoId=None):
        videoInfo = None
        if not streamId:
            videoInfo = self.videoInfo(videoId)
            streamId = 'v%s' %videoInfo['redirect_api_id']
        streamInfoJson = self.streamInfo(streamId)
        streamInfo = StreamInfo(streamInfoJson)
        return streamInfo
    def streamInfo(self, streamId): #v3691491
        url = 'https://api.twitch.tv/kraken/videos/%s' % streamId
        self._log(url)
        return jsonRequest(url)
    def videoInfo(self, videoId): #a611375915
        url = 'http://api.twitch.tv/api/videos/%s' % videoId
        self._log(url)
        return jsonRequest(url)

class StreamInfo():
    def __init__(self, streamInfoJson):
        self.streamId = streamInfoJson['_id']
        self.recordedAt = streamInfoJson['recorded_at']
        self.recordedAtMs = datetimeStringToLong(self.recordedAt)

class Log():
    def __init__(self, streamId, part, recordedAtMs):
        self.streamId = streamId
        self.part = part
        self.recordedAtMs = recordedAtMs
        self.partStartMs = self.recordedAtMs + (self.part - 1) * PART_DURATION
        self.partEndMs = self.partStartMs + PART_DURATION + HIGHEST_DELAY
        self.messages = self.loadReChatMessages()
    def loadReChatMessages(self):
        rechatMessages = lambda rechatResponse: rechatResponse["hits"]["hits"]
        filePath = CACHE_PATH + self.streamId + '_' + str(self.part) + '.json'
        try: msgs = jsonRead(filePath)
        except:
            msgs = list()
            response = self.searchRechatAfter(longToDatetimeString(self.partStartMs))
            msgs = msgs + rechatMessages(response)
            # d.dialog(len(msgs))
            while(datetimeStringToLong(msgs[len(msgs) - 1]['_source']['recieved_at']) < self.partEndMs):
                response = self.searchRechatAfter(msgs[len(msgs) - 1]['_source']['recieved_at'])
                responseMessages = rechatMessages(response)
                if len(responseMessages) == 0:
                    d.dialog('breaking out of ' + str(self.part) + ' because no more messages found')
                    break
                msgs = msgs + responseMessages
                # d.dialog(len(msgs))
            jsonDump(filePath, msgs)
        return msgs
    # v3685179
    def searchRechat(self): return jsonRequest('http://search.rechat.org/videos/' + self.streamId)
    def searchRechatAfter(self, after):
        url = 'http://search.rechat.org/videos/' + self.streamId + '?after=' + urllib.quote_plus(after)
        d.log('url: ' + url)
        return jsonRequest(url)

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

# d.dialog(datetimeStringToLong('2015-01-15T14:32:47Z'))
# d.dialog(datetimeStringToLong('2015-01-15T14:32:47.650Z'))
# tVideo = TwitchVideo('a611375915', '02')
# d.dialog(tVideo.videoId)
# d.dialog(tVideo.streamId)
# d.dialog(tVideo.recordedAt)
# d.dialog(len(tVideo.messages))
