from nepattern.main import INTEGER
from arclet.alconna import argv_config, set_default_argv_type
from nepattern import URL, BasePattern, PatternModel, UnionPattern
from nonebot.adapters.mirai2.message import BaseMessage, MessageChain, MessageSegment

from nonebot_plugin_alconna.argv import MessageArgv
from nonebot_plugin_alconna.typings import SegmentPattern


class MiraiMessageArgv(MessageArgv):
    ...


set_default_argv_type(MiraiMessageArgv)
argv_config(
    MiraiMessageArgv,
    filter_out=[],
    checker=lambda x: isinstance(x, BaseMessage),
    to_text=lambda x: x if x.__class__ is str else str(x) if x.is_text() else None,
    converter=lambda x: MessageChain(x),
)

Source = SegmentPattern("Source", MessageSegment, MessageSegment.source)
Quote = SegmentPattern("Quote", MessageSegment, MessageSegment.quote)
Plain = str
At = SegmentPattern("At", MessageSegment, MessageSegment.at)
AtAll = SegmentPattern("AtAll", MessageSegment, MessageSegment.at_all)
Face = SegmentPattern("Face", MessageSegment, MessageSegment.face)
Image = SegmentPattern("Image", MessageSegment, MessageSegment.image)
FlashImage = SegmentPattern("FlashImage", MessageSegment, MessageSegment.flash_image)
Voice = SegmentPattern("Voice", MessageSegment, MessageSegment.voice)
Xml = SegmentPattern("Xml", MessageSegment, MessageSegment.xml)
Json = SegmentPattern("Json", MessageSegment, MessageSegment.json)
App = SegmentPattern("App", MessageSegment, MessageSegment.app)
Dice = SegmentPattern("Dice", MessageSegment, MessageSegment.Dice)
Poke = SegmentPattern("Poke", MessageSegment, MessageSegment.poke)
MarketFace = SegmentPattern("MarketFace", MessageSegment, MessageSegment.market_face)
MusicShare = SegmentPattern("MusicShare", MessageSegment, MessageSegment.music_share)
Forward = SegmentPattern("Forward", MessageSegment, MessageSegment.forward)
File = SegmentPattern("File", MessageSegment, MessageSegment.file)
MiraiCode = SegmentPattern("MiraiCode", MessageSegment, MessageSegment.mirai_code)


ImgOrUrl = (
    UnionPattern(
        [
            BasePattern(
                model=PatternModel.TYPE_CONVERT,
                origin=str,
                converter=lambda _, x: x.data["url"],
                alias="img",
                accepts=[Image],
            ),
            URL,
        ]
    )
    @ "img_url"
)
"""
内置类型, 允许传入图片元素(Image)或者链接(URL)，返回链接
"""

AtID = (
    UnionPattern(
        [
            BasePattern(
                model=PatternModel.TYPE_CONVERT,
                origin=int,
                alias="At",
                accepts=[At],
                converter=lambda _, x: int(x.data["target"]),
            ),
            BasePattern(
                r"@(\d+)",
                model=PatternModel.REGEX_CONVERT,
                origin=int,
                alias="@xxx",
                accepts=[str],
            ),
            INTEGER,
        ]
    )
    @ "at_id"
)
"""
内置类型，允许传入提醒元素(At)或者'@xxxx'式样的字符串或者数字, 返回数字
"""
