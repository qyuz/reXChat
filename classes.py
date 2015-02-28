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
import common
import dateutil.relativedelta
import dateutil.parser
from common import jsonRequest, jsonRead, jsonDump, datetimeStringToLong, longToDatetimeString


CACHE_PATH = 'special://temp/reXChat/' #DONT FORGET Cache.CACHE_PATH
CACHE_PATH_TRANSLATE = xbmc.translatePath(CACHE_PATH)
ENABLE_CACHE = True
HIGHEST_DELAY = 30000
PART_DURATION = 1711650

d = common.Debugger()
addon = xbmcaddon.Addon()
addonname = addon.getAddonInfo('name')
addonpath = xbmc.translatePath(addon.getAddonInfo('path'))



# d.dialog(datetimeStringToLong('2015-01-15T14:32:47Z'))
# d.dialog(datetimeStringToLong('2015-01-15T14:32:47.650Z'))
# tVideo = TwitchVideo('a611375915', '02')
# d.dialog(tVideo.videoId)
# d.dialog(tVideo.streamId)
# d.dialog(tVideo.recordedAt)
# d.dialog(len(tVideo.messages))

