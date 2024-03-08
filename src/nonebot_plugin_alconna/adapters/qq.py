from nonebot.compat import type_validate_python
from nonebot.adapters.qq.models import MessageArk
from nonebot.adapters.qq.message import Ark as _Ark
from nonebot.adapters.qq.message import MessageSegment
from nonebot.adapters.qq.message import Embed as _Embed
from nonebot.adapters.qq.message import Emoji as _Emoji
from nonebot.adapters.qq.message import Keyboard as _Keyboard
from nonebot.adapters.qq.message import Markdown as _Markdown
from nonebot.adapters.qq.message import Reference as _Reference
from nonebot.adapters.qq.message import Attachment as _Attachment
from nonebot.adapters.qq.message import MentionUser as _MentionUser
from nonebot.adapters.qq.message import MentionChannel as _MentionChannel
from nonebot.adapters.qq.message import LocalAttachment as _LocalAttachment
from nonebot.adapters.qq.message import MentionEveryone as _MentionEveryone

from nonebot_plugin_alconna.uniseg import At
from nonebot_plugin_alconna.uniseg import Hyper
from nonebot_plugin_alconna.uniseg import Text, AtAll
from nonebot_plugin_alconna.uniseg import Other, Reply
from nonebot_plugin_alconna.uniseg import File as UniFile
from nonebot_plugin_alconna.uniseg import Audio as UniAudio
from nonebot_plugin_alconna.uniseg import Emoji as UniEmoji
from nonebot_plugin_alconna.uniseg import Image as UniImage
from nonebot_plugin_alconna.uniseg import Video as UniVideo
from nonebot_plugin_alconna.typings import SegmentPattern, TextSegmentPattern

Ark = SegmentPattern(
    "ark",
    _Ark,
    Hyper,
    MessageSegment.ark,
    handle=lambda x: MessageSegment.ark(type_validate_python(MessageArk, x.content)),
)
Embed = SegmentPattern("embed", _Embed, Other, MessageSegment.embed)
Emoji = SegmentPattern("emoji", _Emoji, UniEmoji, MessageSegment.emoji)
Image = SegmentPattern("image", _Attachment, UniImage, MessageSegment.image)
FileImage = SegmentPattern("file_image", _LocalAttachment, UniImage, MessageSegment.file_image)
Audio = SegmentPattern("audio", _Attachment, UniAudio, MessageSegment.audio)
FileAudio = SegmentPattern("file_audio", _LocalAttachment, UniAudio, MessageSegment.file_audio)
Video = SegmentPattern("video", _Attachment, UniVideo, MessageSegment.video)
FileVideo = SegmentPattern("file_video", _LocalAttachment, UniVideo, MessageSegment.file_video)
File = SegmentPattern("file", _Attachment, UniFile, MessageSegment.file)
FileFile = SegmentPattern("file_file", _LocalAttachment, UniFile, MessageSegment.file_file)
Keyboard = SegmentPattern("keyboard", _Keyboard, Other, MessageSegment.keyboard)
MentionUser = SegmentPattern("mention_user", _MentionUser, At, MessageSegment.mention_user)
MentionChannel = SegmentPattern("mention_channel", _MentionChannel, At, MessageSegment.mention_channel)
MentionEveryone = SegmentPattern("mention_everyone", _MentionEveryone, AtAll, MessageSegment.mention_everyone)
Reference = SegmentPattern("reference", _Reference, Reply, MessageSegment.reference)


def markdown(self, x: Text):
    if x.extract_most_style() == "markdown":
        return MessageSegment.markdown(x.text)


Markdown = TextSegmentPattern("markdown", _Markdown, MessageSegment.markdown, markdown)
