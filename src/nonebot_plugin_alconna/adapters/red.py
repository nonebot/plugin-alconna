from nonebot.adapters.red.message import MessageSegment

from nonebot_plugin_alconna.uniseg import Other
from nonebot_plugin_alconna.uniseg import Reference
from nonebot_plugin_alconna.uniseg import At as UniAt
from nonebot_plugin_alconna.uniseg import Emoji, Hyper
from nonebot_plugin_alconna.typings import SegmentPattern
from nonebot_plugin_alconna.uniseg import File as UniFile
from nonebot_plugin_alconna.uniseg import AtAll as UniAtAll
from nonebot_plugin_alconna.uniseg import Image as UniImage
from nonebot_plugin_alconna.uniseg import Reply as UniReply
from nonebot_plugin_alconna.uniseg import Video as UniVideo
from nonebot_plugin_alconna.uniseg import Voice as UniVoice

At = SegmentPattern("at", MessageSegment, UniAt, MessageSegment.at)
AtAll = SegmentPattern("at_all", MessageSegment, UniAtAll, MessageSegment.at_all)
Face = SegmentPattern("face", MessageSegment, Emoji, MessageSegment.face)
Image = SegmentPattern("image", MessageSegment, UniImage, MessageSegment.image)
File = SegmentPattern("file", MessageSegment, UniFile, MessageSegment.file)
Voice = SegmentPattern("voice", MessageSegment, UniVoice, MessageSegment.voice)
Video = SegmentPattern("video", MessageSegment, UniVideo, MessageSegment.video)
Reply = SegmentPattern("reply", MessageSegment, UniReply, MessageSegment.reply)
Ark = SegmentPattern("ark", MessageSegment, Hyper, MessageSegment.ark)
MarketFace = SegmentPattern("market_face", MessageSegment, Other, MessageSegment.market_face)
Forward = SegmentPattern("forward", MessageSegment, Reference, MessageSegment.forward)
