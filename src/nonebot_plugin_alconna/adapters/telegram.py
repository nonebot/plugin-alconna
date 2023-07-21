from nepattern import UnionPattern
from arclet.alconna import argv_config, set_default_argv_type
from nonebot.adapters.telegram.message import (
    File,
    Entity,
    Message,
    BaseMessage,
    UnCombinFile,
    MessageSegment,
)

from nonebot_plugin_alconna.argv import MessageArgv
from nonebot_plugin_alconna.typings import SegmentPattern


class TelegramMessageArgv(MessageArgv):
    ...


def is_text(x: MessageSegment):
    return x.type in {
        "text",
        "bold",
        "italic",
        "underline",
        "strikethrough",
        "spoiler",
        "code",
    }


set_default_argv_type(TelegramMessageArgv)
argv_config(
    TelegramMessageArgv,
    filter_out=[],
    checker=lambda x: isinstance(x, BaseMessage),
    to_text=lambda x: x if x.__class__ is str else str(x) if is_text(x) else None,
    converter=lambda x: Message(x),
)

Text = str
Location = SegmentPattern("location", MessageSegment, MessageSegment.location)
Venue = SegmentPattern("venue", MessageSegment, MessageSegment.venue)
Poll = SegmentPattern("poll", MessageSegment, MessageSegment.poll)
Dice = SegmentPattern("dice", MessageSegment, MessageSegment.dice)
ChatAction = SegmentPattern("chat_action", MessageSegment, MessageSegment.chat_action)

Mention = SegmentPattern("mention", Entity, Entity.mention)
Hashtag = SegmentPattern("hashtag", Entity, Entity.hashtag)
Cashtag = SegmentPattern("cashtag", Entity, Entity.cashtag)
BotCommand = SegmentPattern("bot_command", Entity, Entity.bot_command)
Url = SegmentPattern("url", Entity, Entity.url)
Email = SegmentPattern("email", Entity, Entity.email)
PhoneNumber = SegmentPattern("phone_number", Entity, Entity.phone_number)
Bold = SegmentPattern("bold", Entity, Entity.bold)
"""该 Pattern 只用于发送"""
Italic = SegmentPattern("italic", Entity, Entity.italic)
"""该 Pattern 只用于发送"""
Underline = SegmentPattern("underline", Entity, Entity.underline)
"""该 Pattern 只用于发送"""
Strikethrough = SegmentPattern("strikethrough", Entity, Entity.strikethrough)
"""该 Pattern 只用于发送"""
Spoiler = SegmentPattern("spoiler", Entity, Entity.spoiler)
"""该 Pattern 只用于发送"""
Code = SegmentPattern("code", Entity, Entity.code)
"""该 Pattern 只用于发送"""
Pre = SegmentPattern("pre", Entity, Entity.pre)
TextLink = SegmentPattern("text_link", Entity, Entity.text_link)
TextMention = SegmentPattern("text_mention", Entity, Entity.text_mention)
CustomEmoji = SegmentPattern("custom_emoji", Entity, Entity.custom_emoji)

Image = Photo = SegmentPattern("photo", File, File.photo)
Voice = SegmentPattern("voice", File, File.voice)
Animation = SegmentPattern("animation", File, File.animation)
Audio = SegmentPattern("audio", File, File.audio)
Document = SegmentPattern("document", File, File.document)
Video = SegmentPattern("video", File, File.video)

Sticker = SegmentPattern("sticker", UnCombinFile, UnCombinFile.sticker)
VideoNote = SegmentPattern("video_note", UnCombinFile, UnCombinFile.video_note)

Mentions = UnionPattern([Mention, TextMention, TextLink])
"""联合接收 Mention, TextMention, TextLink, 不能用于发送"""

Videos = UnionPattern([Video, Animation])
"""联合接收 Video, Animation, 不能用于发送"""
