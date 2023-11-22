from nepattern.main import URL, INTEGER
from nonebot.adapters.qq.message import Ark as _Ark
from nonebot.adapters.qq.message import MessageSegment
from nonebot.adapters.qq.message import Embed as _Embed
from nonebot.adapters.qq.message import Emoji as _Emoji
from nepattern import BasePattern, PatternModel, UnionPattern
from nonebot.adapters.qq.message import Keyboard as _Keyboard
from nonebot.adapters.qq.message import Markdown as _Markdown
from nonebot.adapters.qq.message import Reference as _Reference
from nonebot.adapters.qq.message import Attachment as _Attachment
from nonebot.adapters.qq.message import MentionUser as _MentionUser
from nonebot.adapters.qq.message import MentionChannel as _MentionChannel
from nonebot.adapters.qq.message import LocalAttachment as _LocalAttachment
from nonebot.adapters.qq.message import MentionEveryone as _MentionEveryone

from nonebot_plugin_alconna.typings import SegmentPattern

Text = str
Ark = SegmentPattern("ark", _Ark, MessageSegment.ark)
Embed = SegmentPattern("embed", _Embed, MessageSegment.embed)
Emoji = SegmentPattern("emoji", _Emoji, MessageSegment.emoji)
Image = SegmentPattern("image", _Attachment, MessageSegment.image)
FileImage = SegmentPattern("file_image", _LocalAttachment, MessageSegment.file_image)
Audio = SegmentPattern("audio", _Attachment, MessageSegment.audio)
FileAudio = SegmentPattern("file_audio", _LocalAttachment, MessageSegment.file_audio)
Video = SegmentPattern("video", _Attachment, MessageSegment.video)
FileVideo = SegmentPattern("file_video", _LocalAttachment, MessageSegment.file_video)
File = SegmentPattern("file", _Attachment, MessageSegment.file)
FileFile = SegmentPattern("file_file", _LocalAttachment, MessageSegment.file_file)
Keyboard = SegmentPattern("keyboard", _Keyboard, MessageSegment.keyboard)
Markdown = SegmentPattern("markdown", _Markdown, MessageSegment.markdown)
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
