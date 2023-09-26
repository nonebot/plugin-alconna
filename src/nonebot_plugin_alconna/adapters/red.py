from nepattern.main import INTEGER
from nonebot.adapters.red.message import  MessageSegment
from nepattern import URL, BasePattern, PatternModel, UnionPattern

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


ImgOrUrl = (
    UnionPattern(
        [
            BasePattern(
                model=PatternModel.TYPE_CONVERT,
                origin=str,
                converter=lambda _, x: f"https://gchat.qpic.cn/gchatpic_new/0/0-0-{x.data['md5'].upper()}/0",
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
