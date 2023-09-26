from nepattern.main import INTEGER
from nonebot.adapters.mirai2.message import MessageSegment
from nepattern import URL, BasePattern, PatternModel, UnionPattern

from nonebot_plugin_alconna.typings import SegmentPattern

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
                converter=lambda _, x: int(x[1]),
            ),
            INTEGER,
        ]
    )
    @ "at_id"
)
"""
内置类型，允许传入提醒元素(At)或者'@xxxx'式样的字符串或者数字, 返回数字
"""
