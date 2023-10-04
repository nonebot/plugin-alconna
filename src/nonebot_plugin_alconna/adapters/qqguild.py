import warnings

warnings.warn(
    "~adapters.qqguild is deprecated, " "use ~adapters.qq instead.",
    DeprecationWarning,
    stacklevel=2,
)

from nepattern.main import URL, INTEGER
from nonebot.adapters.qqguild.message import Ark as _Ark
from nonebot.adapters.qqguild.message import MessageSegment
from nonebot.adapters.qqguild.message import Embed as _Embed
from nonebot.adapters.qqguild.message import Emoji as _Emoji
from nepattern import BasePattern, PatternModel, UnionPattern
from nonebot.adapters.qqguild.message import Reference as _Reference
from nonebot.adapters.qqguild.message import Attachment as _Attachment
from nonebot.adapters.qqguild.message import LocalImage as _LocalImage
from nonebot.adapters.qqguild.message import MentionUser as _MentionUser
from nonebot.adapters.qqguild.message import MentionChannel as _MentionChannel
from nonebot.adapters.qqguild.message import MentionEveryone as _MentionEveryone

from nonebot_plugin_alconna.typings import SegmentPattern

Text = str
Ark = SegmentPattern("ark", _Ark, MessageSegment.ark)
Embed = SegmentPattern("embed", _Embed, MessageSegment.embed)
Emoji = SegmentPattern("emoji", _Emoji, MessageSegment.emoji)
Image = SegmentPattern("attachment", _Attachment, MessageSegment.image)
FileImage = SegmentPattern("file_image", _LocalImage, MessageSegment.file_image)
MentionUser = SegmentPattern("mention_user", _MentionUser, MessageSegment.mention_user)
MentionChannel = SegmentPattern("mention_channel", _MentionChannel, MessageSegment.mention_channel)
MentionEveryone = SegmentPattern("mention_everyone", _MentionEveryone, MessageSegment.mention_everyone)
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
                converter=lambda _, x: int(x[1]),
            ),
            INTEGER,
        ]
    )
    @ "mention_id"
)
"""
内置类型，允许传入提醒元素(Mention)或者'@xxxx'式样的字符串或者数字, 返回数字
"""
