from nepattern.main import INTEGER
from nonebot.adapters.onebot.v11.message import MessageSegment
from nepattern import URL, BasePattern, PatternModel, UnionPattern

from nonebot_plugin_alconna.typings import SegmentPattern

Anonymous = SegmentPattern("anonymous", MessageSegment, MessageSegment.anonymous)
Text = str
At = SegmentPattern("at", MessageSegment, MessageSegment.at, additional=lambda x: x.data["qq"] != "all")
AtAll = SegmentPattern(
    "at", MessageSegment, lambda: MessageSegment.at("all"), additional=lambda x: x.data["qq"] == "all"
)
Contact = SegmentPattern("contact", MessageSegment, MessageSegment.contact)
Dice = SegmentPattern("dice", MessageSegment, MessageSegment.dice)
Face = SegmentPattern("face", MessageSegment, MessageSegment.face)
Forward = SegmentPattern("forward", MessageSegment, MessageSegment.forward)
Image = SegmentPattern("image", MessageSegment, MessageSegment.image)
Json = SegmentPattern("json", MessageSegment, MessageSegment.json)
Location = SegmentPattern("location", MessageSegment, MessageSegment.location)
Music = SegmentPattern("music", MessageSegment, MessageSegment.music)
Node = SegmentPattern("node", MessageSegment, MessageSegment.node)
Poke = SegmentPattern("poke", MessageSegment, MessageSegment.poke)
Record = SegmentPattern("record", MessageSegment, MessageSegment.record)
Reply = SegmentPattern("reply", MessageSegment, MessageSegment.reply)
RPS = SegmentPattern("rps", MessageSegment, MessageSegment.rps)
Shake = SegmentPattern("shake", MessageSegment, MessageSegment.shake)
Share = SegmentPattern("share", MessageSegment, MessageSegment.share)
Video = SegmentPattern("video", MessageSegment, MessageSegment.video)
Xml = SegmentPattern("xml", MessageSegment, MessageSegment.xml)


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
                converter=lambda _, x: int(x.data["qq"]),
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
