from nepattern.main import URL, INTEGER
from arclet.alconna import argv_config, set_default_argv_type
from nepattern import BasePattern, PatternModel, UnionPattern
from nonebot.adapters.onebot.v12.message import Message, BaseMessage, MessageSegment

from nonebot_plugin_alconna.argv import MessageArgv
from nonebot_plugin_alconna.typings import SegmentPattern


class Ob12MessageArgv(MessageArgv):
    ...


set_default_argv_type(Ob12MessageArgv)
argv_config(
    Ob12MessageArgv,
    filter_out=[],
    checker=lambda x: isinstance(x, BaseMessage),
    to_text=lambda x: x if x.__class__ is str else str(x) if x.is_text() else None,
    converter=lambda x: Message(x),
)
Text = str
Mention = SegmentPattern("mention", MessageSegment, MessageSegment.mention)
MentionAll = SegmentPattern("mention_all", MessageSegment, MessageSegment.mention_all)
Image = SegmentPattern("image", MessageSegment, MessageSegment.image)
Audio = SegmentPattern("audio", MessageSegment, MessageSegment.audio)
Voice = SegmentPattern("voice", MessageSegment, MessageSegment.voice)
File = SegmentPattern("file", MessageSegment, MessageSegment.file)
Video = SegmentPattern("video", MessageSegment, MessageSegment.video)
Location = SegmentPattern("location", MessageSegment, MessageSegment.location)
Reply = SegmentPattern("reply", MessageSegment, MessageSegment.reply)

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

MentionID = (
    UnionPattern(
        [
            BasePattern(
                model=PatternModel.TYPE_CONVERT,
                origin=int,
                alias="Mention",
                accepts=[Mention],
                converter=lambda _, x: int(x.data["user_id"]),
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
    @ "mention_id"
)
"""
内置类型，允许传入提醒元素(Mention)或者'@xxxx'式样的字符串或者数字, 返回数字
"""
