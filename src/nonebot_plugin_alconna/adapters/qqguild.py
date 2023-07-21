from nepattern.main import URL, INTEGER
from nonebot.adapters.qqguild.message import Message
from nonebot.adapters.qqguild.message import Ark as _Ark
from nonebot.adapters.qqguild.message import BaseMessage
from nonebot.adapters.qqguild.message import MessageSegment
from nonebot.adapters.qqguild.message import Embed as _Embed
from nonebot.adapters.qqguild.message import Emoji as _Emoji
from arclet.alconna import argv_config, set_default_argv_type
from nepattern import BasePattern, PatternModel, UnionPattern
from nonebot.adapters.qqguild.message import Reference as _Reference
from nonebot.adapters.qqguild.message import Attachment as _Attachment
from nonebot.adapters.qqguild.message import LocalImage as _LocalImage
from nonebot.adapters.qqguild.message import MentionUser as _MentionUser
from nonebot.adapters.qqguild.message import MentionChannel as _MentionChannel
from nonebot.adapters.qqguild.message import MentionEveryone as _MentionEveryone

from nonebot_plugin_alconna.argv import MessageArgv
from nonebot_plugin_alconna.typings import SegmentPattern


class QQGuildMessageArgv(MessageArgv):
    ...


set_default_argv_type(QQGuildMessageArgv)
argv_config(
    QQGuildMessageArgv,
    filter_out=[],
    checker=lambda x: isinstance(x, BaseMessage),
    to_text=lambda x: x if x.__class__ is str else str(x) if x.is_text() else None,
    converter=lambda x: Message(x),
)


Text = str
Ark = SegmentPattern("ark", _Ark, MessageSegment.ark)
Embed = SegmentPattern("embed", _Embed, MessageSegment.embed)
Emoji = SegmentPattern("emoji", _Emoji, MessageSegment.emoji)
Image = SegmentPattern("attachment", _Attachment, MessageSegment.image)
FileImage = SegmentPattern("file_image", _LocalImage, MessageSegment.file_image)
MentionUser = SegmentPattern("mention_user", _MentionUser, MessageSegment.mention_user)
MentionChannel = SegmentPattern(
    "mention_channel", _MentionChannel, MessageSegment.mention_channel
)
MentionEveryone = SegmentPattern(
    "mention_everyone", _MentionEveryone, MessageSegment.mention_everyone
)
Reference = SegmentPattern("reference", _Reference, MessageSegment.reference)


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
                alias="MentionUser",
                accepts=[MentionUser],
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
