import common
from common import Report, Test
from rechat import CachedService, Message, Service
from twitch import API, CachedAPI, StreamInfo

d = common.Debugger()

testRunner = Test(Report.SUMMARY, True)
twitchChannel = 'cereth'
videoLength = 1000
twitchAPI = API()
cachedTwitchAPI = CachedAPI()

#DATETIME
testRunner.test(common.datetimeStringToLong("2015-01-15T14:32:47.650Z") == 1421332367650,
    "Datetime conversion to Long")
testRunner.test(common.longToDatetimeString(1421332367650) == "2015-01-15T14:32:47.650Z",
    "Long conversion to Datetime")


#TWITCH API
streamInfo = twitchAPI.getStreamInfo(streamId='v3691491')
testRunner.test(streamInfo.recordedAt == "2015-01-15T14:01:36Z",
    "RecordedAt field should match",
    streamInfo)

#deprecated?
#videoStreamInfo = twitchAPI.getStreamInfo(videoId='a611375915')
#testRunner.test(videoStreamInfo.recordedAt == streamInfo.recordedAt,
#    "Stream from video and stream info should have same recordedAt field value",
#    obj= { 'videoStreamInfo': videoStreamInfo, 'streamInfo': streamInfo })

broadcasts = twitchAPI.getBroadcasts(twitchChannel)
broadcastVideos = broadcasts['videos']
twitchVideo = next((video for video in broadcastVideos if lambda video: video['length'] >= videoLength), None)

testRunner.test(twitchVideo,
    "Broadcast video shouldnt be None",
    obj=broadcasts)

streamId = twitchVideo['_id']
streamInfo = twitchAPI.getStreamInfo(streamId=streamId)

#RECHAT
rechatService = Service(streamInfo)
rechatMessages = rechatService.next()

testRunner.test(len(rechatMessages) == 500,
    "Rechat Service should return 500 messages",
    rechatMessages)

rechatMessage = rechatMessages[0]
message = Message(rechatMessage, 0)

testRunner.test(len(message.receivedAt) > 0,
    "Received at in Message should be populated",
    rechatMessage)
testRunner.test(len(message.sender) > 0,
    "Sender in Message should be populated",
    rechatMessage)
testRunner.test(len(message.text) > 0,
    "Text in Message should be populated",
    rechatMessage)

testRunner.go()