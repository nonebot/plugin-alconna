from nonebot.adapters.kritor.message import MessageSegment
from nonebot.adapters.kritor.message import Markdown as _Markdown

from nonebot_plugin_alconna.uniseg import Text
from nonebot_plugin_alconna.uniseg import Other
from nonebot_plugin_alconna.uniseg import Reference
from nonebot_plugin_alconna.uniseg import At as UniAt
from nonebot_plugin_alconna.uniseg import Emoji, Hyper
from nonebot_plugin_alconna.uniseg import AtAll as UniAtAll
from nonebot_plugin_alconna.uniseg import Image as UniImage
from nonebot_plugin_alconna.uniseg import Reply as UniReply
from nonebot_plugin_alconna.uniseg import Video as UniVideo
from nonebot_plugin_alconna.uniseg import Voice as UniVoice
from nonebot_plugin_alconna.typings import SegmentPattern, TextSegmentPattern

At = SegmentPattern(
    "at",
    MessageSegment,
    UniAt,
    MessageSegment.at,
    additional=lambda x: x.origin is not None and x.origin.data["qq"] != "all",
)
AtAll = SegmentPattern(
    "at",
    MessageSegment,
    UniAtAll,
    lambda: MessageSegment.at("all"),
    additional=lambda x: x.origin is not None and x.origin.data["qq"] == "all",
)
Contact = SegmentPattern("contact", MessageSegment, Other, MessageSegment.contact)
Dice = SegmentPattern("dice", MessageSegment, Other, MessageSegment.dice)
RPS = SegmentPattern("rps", MessageSegment, Other, MessageSegment.rps)
Basketball = SegmentPattern("basketball", MessageSegment, Other, MessageSegment.basketball)
Face = SegmentPattern("face", MessageSegment, Emoji, MessageSegment.face)
Forward = SegmentPattern("forward", MessageSegment, Reference, MessageSegment.forward)
Image = SegmentPattern("image", MessageSegment, UniImage, MessageSegment.image)
Json = SegmentPattern("json", MessageSegment, Hyper, MessageSegment.json)
Music = SegmentPattern("music", MessageSegment, Other, MessageSegment.music)
Poke = SegmentPattern("poke", MessageSegment, Other, MessageSegment.poke)
Record = SegmentPattern("voice", MessageSegment, UniVoice, MessageSegment.voice)
Reply = SegmentPattern("reply", MessageSegment, UniReply, MessageSegment.reply)
Share = SegmentPattern("share", MessageSegment, Other, MessageSegment.share)
Video = SegmentPattern("video", MessageSegment, UniVideo, MessageSegment.video)
Xml = SegmentPattern("xml", MessageSegment, Hyper, MessageSegment.xml)
Location = SegmentPattern("location", MessageSegment, Other, MessageSegment.location)
Weather = SegmentPattern("weather", MessageSegment, Other, MessageSegment.weather)
Keyboard = SegmentPattern("keyboard", MessageSegment, Other, MessageSegment.keyboard)


def markdown(self, x: Text):
    if x.extract_most_style() == "markdown":
        return MessageSegment.markdown(x.text)


Markdown = TextSegmentPattern("markdown", _Markdown, MessageSegment.markdown, markdown)
