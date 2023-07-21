from nepattern.main import INTEGER
from arclet.alconna import argv_config, set_default_argv_type
from nepattern import URL, BasePattern, PatternModel, UnionPattern
from nonebot.adapters.onebot.v11.message import Message, BaseMessage, MessageSegment

from nonebot_plugin_alconna.argv import MessageArgv
from nonebot_plugin_alconna.typings import SegmentPattern


class Ob11MessageArgv(MessageArgv):
    ...


set_default_argv_type(Ob11MessageArgv)
argv_config(
    Ob11MessageArgv,
    filter_out=[],
    checker=lambda x: isinstance(x, BaseMessage),
    to_text=lambda x: x if x.__class__ is str else str(x) if x.is_text() else None,
    converter=lambda x: Message(x),
)

Anonymous = SegmentPattern("anonymous", MessageSegment, MessageSegment.anonymous)
Text = str
At = SegmentPattern("at", MessageSegment, MessageSegment.at)
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
            ),
            INTEGER,
        ]
    )
    @ "at_id"
)
"""
内置类型，允许传入提醒元素(At)或者'@xxxx'式样的字符串或者数字, 返回数字
"""
