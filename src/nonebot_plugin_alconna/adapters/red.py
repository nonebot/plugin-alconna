from nepattern.main import INTEGER
from nonebot.adapters.red.message import MessageSegment
from nepattern import BasePattern, PatternModel, UnionPattern

from nonebot_plugin_alconna.typings import SegmentPattern

Text = str
At = SegmentPattern("at", MessageSegment, MessageSegment.at)
AtAll = SegmentPattern("at_all", MessageSegment, MessageSegment.at_all)
Face = SegmentPattern("face", MessageSegment, MessageSegment.face)
Image = SegmentPattern("image", MessageSegment, MessageSegment.image)
File = SegmentPattern("file", MessageSegment, MessageSegment.file)
Voice = SegmentPattern("voice", MessageSegment, MessageSegment.voice)
Video = SegmentPattern("video", MessageSegment, MessageSegment.video)
Reply = SegmentPattern("reply", MessageSegment, MessageSegment.reply)
Ark = SegmentPattern("ark", MessageSegment, MessageSegment.ark)
MarketFace = SegmentPattern("market_face", MessageSegment, MessageSegment.market_face)
Forward = SegmentPattern("forward", MessageSegment, MessageSegment.forward)


AtID = (
    UnionPattern(
        [
            BasePattern(
                model=PatternModel.TYPE_CONVERT,
                origin=int,
                alias="At",
                accepts=[At],
                converter=lambda _, x: int(x.data["user_id"]),
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
