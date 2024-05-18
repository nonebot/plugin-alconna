from nonebot.adapters.feishu.message import MessageSegment

from nonebot_plugin_alconna.uniseg import Hyper
from nonebot_plugin_alconna.uniseg import Other
from nonebot_plugin_alconna.uniseg import At as UniAt
from nonebot_plugin_alconna.typings import SegmentPattern
from nonebot_plugin_alconna.uniseg import File as UniFile
from nonebot_plugin_alconna.uniseg import AtAll as UniAtAll
from nonebot_plugin_alconna.uniseg import Audio as UniAudio
from nonebot_plugin_alconna.uniseg import Image as UniImage
from nonebot_plugin_alconna.uniseg import Video as UniVideo

Text = str
At = SegmentPattern("at", MessageSegment, UniAt, MessageSegment.at)
AtAll = SegmentPattern(
    "at",
    MessageSegment,
    UniAtAll,
    lambda: MessageSegment.at("all"),
    additional=lambda x: (x.origin is not None and x.origin.data["user_id"] == "all"),
)
AtHere = SegmentPattern(
    "at",
    MessageSegment,
    UniAtAll,
    lambda: MessageSegment.at("here"),
    additional=lambda x: (x.origin is not None and x.origin.data["user_id"] == "here"),
)
Post = SegmentPattern("post", MessageSegment, Hyper, MessageSegment.post)
Image = SegmentPattern("image", MessageSegment, UniImage, MessageSegment.image)
Interactive = SegmentPattern("interactive", MessageSegment, Other, MessageSegment.interactive)
ShareChat = SegmentPattern("share_chat", MessageSegment, Other, MessageSegment.share_chat)
ShareUser = SegmentPattern("share_user", MessageSegment, Other, MessageSegment.share_user)
Audio = SegmentPattern("audio", MessageSegment, UniAudio, MessageSegment.audio)
Video = Media = SegmentPattern("media", MessageSegment, UniVideo, MessageSegment.media)
File = SegmentPattern("File", MessageSegment, UniFile, MessageSegment.file)
Sticker = SegmentPattern("sticker", MessageSegment, Other, MessageSegment.sticker)
