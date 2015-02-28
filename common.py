import calendar, datetime, dateutil, dateutil.parser, json, os, re, urllib, xbmc, xbmcgui, xbmcvfs

ENABLE_CACHE = True #remove this

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