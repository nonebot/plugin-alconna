from nonebot.adapters.ntchat.message import MessageSegment  # type: ignore

from nonebot_plugin_alconna.uniseg import Hyper
from nonebot_plugin_alconna.uniseg import Other
from nonebot_plugin_alconna.typings import SegmentPattern
from nonebot_plugin_alconna.uniseg import File as UniFile
from nonebot_plugin_alconna.uniseg import Image as UniImage
from nonebot_plugin_alconna.uniseg import Video as UniVideo

RoomAtMsg = SegmentPattern("room_at_msg", MessageSegment, Other, MessageSegment.room_at_msg)
Card = SegmentPattern(
    "card",
    MessageSegment,
    Hyper,
    MessageSegment.card,
    handle=lambda x: MessageSegment.card(x.content["card_wxid"]),  # type: ignore
)
Link = SegmentPattern(
    "link",
    MessageSegment,
    Hyper,
    MessageSegment.link,
    handle=lambda x: MessageSegment.link(**x.content),  # type: ignore
)
Image = SegmentPattern("image", MessageSegment, UniImage, MessageSegment.image)
File = SegmentPattern("file", MessageSegment, UniFile, MessageSegment.file)
Video = SegmentPattern("video", MessageSegment, UniVideo, MessageSegment.video)
XML = SegmentPattern("xml", MessageSegment, Hyper, MessageSegment.xml)
