from nepattern.main import URL, INTEGER
from arclet.alconna import argv_config, set_default_argv_type
from nepattern import BasePattern, PatternModel, UnionPattern
from nonebot.adapters.discord.message import (
    Message,
    BaseMessage,
    EmbedSegment,
    MessageSegment,
    StickerSegment,
    ComponentSegment,
    ReferenceSegment,
    TimestampSegment,
    AttachmentSegment,
    CustomEmojiSegment,
    MentionRoleSegment,
    MentionUserSegment,
    MentionChannelSegment,
    MentionEveryoneSegment,
)

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
Embed = SegmentPattern("embed", EmbedSegment, MessageSegment.embed)
Sticker = SegmentPattern("sticker", StickerSegment, MessageSegment.sticker)
Component = SegmentPattern("component", ComponentSegment, MessageSegment.component)
Timestamp = SegmentPattern("timestamp", TimestampSegment, MessageSegment.timestamp)
Emoji = SegmentPattern("emoji", CustomEmojiSegment, MessageSegment.custom_emoji)
Image = SegmentPattern("attachment", AttachmentSegment, MessageSegment.attachment)
MentionUser = SegmentPattern("mention_user", MentionUserSegment, MessageSegment.mention_user)
MentionChannel = SegmentPattern(
    "mention_channel", MentionChannelSegment, MessageSegment.mention_channel
)
MentionRole = SegmentPattern("mention_role", MentionRoleSegment, MessageSegment.mention_role)
MentionEveryone = SegmentPattern(
    "mention_everyone", MentionEveryoneSegment, MessageSegment.mention_everyone
)
Reference = SegmentPattern("reference", ReferenceSegment, MessageSegment.reference)


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
