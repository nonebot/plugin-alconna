from nonebot_plugin_alconna.typings import SegmentPattern
from nonebot.adapters.ntchat.message import MessageSegment
from nonebot_plugin_alconna.argv import MessageArgv
from arclet.alconna import set_default_argv_type

set_default_argv_type(MessageArgv)

Text = str
RoomAtMsg = SegmentPattern("room_at_msg", MessageSegment, MessageSegment.room_at_msg)
Card = SegmentPattern("card", MessageSegment, MessageSegment.card)
Link = SegmentPattern("link", MessageSegment, MessageSegment.link)
Image = SegmentPattern("image", MessageSegment, MessageSegment.image)
File = SegmentPattern("file", MessageSegment, MessageSegment.file)
Video = SegmentPattern("video", MessageSegment, MessageSegment.video)
XML = SegmentPattern("xml", MessageSegment, MessageSegment.xml)
