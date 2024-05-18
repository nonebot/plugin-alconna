from nonebot.adapters.mirai.message import MessageSegment
from nonebot.adapters.mirai.message import File as MiraiFile

from nonebot_plugin_alconna.uniseg import Reference
from nonebot_plugin_alconna.uniseg import At as UniAt
from nonebot_plugin_alconna.uniseg import Emoji, Hyper
from nonebot_plugin_alconna.uniseg import Other, Reply
from nonebot_plugin_alconna.typings import SegmentPattern
from nonebot_plugin_alconna.uniseg import File as UniFile
from nonebot_plugin_alconna.uniseg import AtAll as UniAtAll
from nonebot_plugin_alconna.uniseg import Image as UniImage
from nonebot_plugin_alconna.uniseg import Video as UniVideo
from nonebot_plugin_alconna.uniseg import Voice as UniVoice

Quote = SegmentPattern("reply", MessageSegment, Reply, MessageSegment.reply)
Plain = str
At = SegmentPattern("at", MessageSegment, UniAt, MessageSegment.at)
AtAll = SegmentPattern("at_all", MessageSegment, UniAtAll, MessageSegment.at_all)
Face = SegmentPattern("face", MessageSegment, Emoji, MessageSegment.face)
Image = SegmentPattern("image", MessageSegment, UniImage, MessageSegment.image)
FlashImage = SegmentPattern("flash_image", MessageSegment, UniImage, MessageSegment.flash_image)
Voice = SegmentPattern("voice", MessageSegment, UniVoice, MessageSegment.voice)
Video = SegmentPattern("video", MessageSegment, UniVideo, MessageSegment.video)
Xml = SegmentPattern("xml", MessageSegment, Hyper, MessageSegment.xml)
Json = SegmentPattern("json", MessageSegment, Hyper, MessageSegment.json)
App = SegmentPattern("app", MessageSegment, Hyper, MessageSegment.app)
Dice = SegmentPattern("dice", MessageSegment, Other, MessageSegment.dice)
Poke = SegmentPattern("poke", MessageSegment, Other, MessageSegment.poke)
MarketFace = SegmentPattern("market_face", MessageSegment, Other, MessageSegment.market_face)
MusicShare = SegmentPattern("music", MessageSegment, Other, MessageSegment.music)
Forward = SegmentPattern("forward", MessageSegment, Reference, MessageSegment.forward)
File = SegmentPattern("file", MessageSegment, UniFile, MiraiFile)
