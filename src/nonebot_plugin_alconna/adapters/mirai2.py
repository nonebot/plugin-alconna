from nonebot.adapters.mirai2.message import MessageSegment

from nonebot_plugin_alconna.uniseg import Reference
from nonebot_plugin_alconna.uniseg import At as UniAt
from nonebot_plugin_alconna.uniseg import Emoji, Hyper
from nonebot_plugin_alconna.uniseg import Other, Reply
from nonebot_plugin_alconna.typings import SegmentPattern
from nonebot_plugin_alconna.uniseg import File as UniFile
from nonebot_plugin_alconna.uniseg import AtAll as UniAtAll
from nonebot_plugin_alconna.uniseg import Image as UniImage
from nonebot_plugin_alconna.uniseg import Voice as UniVoice

Source = SegmentPattern("Source", MessageSegment, Other, MessageSegment.source)
Quote = SegmentPattern("Quote", MessageSegment, Reply, MessageSegment.quote)
Plain = Text = str
At = SegmentPattern("At", MessageSegment, UniAt, MessageSegment.at)
AtAll = SegmentPattern("AtAll", MessageSegment, UniAtAll, MessageSegment.at_all)
Face = SegmentPattern("Face", MessageSegment, Emoji, MessageSegment.face)
Image = SegmentPattern("Image", MessageSegment, UniImage, MessageSegment.image)
FlashImage = SegmentPattern("FlashImage", MessageSegment, UniImage, MessageSegment.flash_image)
Voice = SegmentPattern("Voice", MessageSegment, UniVoice, MessageSegment.voice)
Xml = SegmentPattern("Xml", MessageSegment, Hyper, MessageSegment.xml)
Json = SegmentPattern("Json", MessageSegment, Hyper, MessageSegment.json)
App = SegmentPattern("App", MessageSegment, Hyper, MessageSegment.app)
Dice = SegmentPattern("Dice", MessageSegment, Other, MessageSegment.Dice)
Poke = SegmentPattern("Poke", MessageSegment, Other, MessageSegment.poke)
MarketFace = SegmentPattern("MarketFace", MessageSegment, Other, MessageSegment.market_face)
MusicShare = SegmentPattern("MusicShare", MessageSegment, Other, MessageSegment.music_share)
Forward = SegmentPattern("Forward", MessageSegment, Reference, MessageSegment.forward)
File = SegmentPattern("File", MessageSegment, UniFile, MessageSegment.file)
