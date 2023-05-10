from nonebot_plugin_alconna.typings import SegmentPattern
from nonebot.adapters.kaiheila.message import MessageSegment, Message, BaseMessage
from nonebot_plugin_alconna.argv import MessageArgv
from arclet.alconna import set_default_argv_type, argv_config


class KookMessageArgv(MessageArgv):
    ...


set_default_argv_type(KookMessageArgv)
argv_config(
    KookMessageArgv,
    filter_out=[],
    checker=lambda x: isinstance(x, BaseMessage),
    to_text=lambda x: x if x.__class__ is str else str(x) if x.is_text() else None,
    converter=lambda x: Message(x)
)

Text = str
At = SegmentPattern("at", MessageSegment, MessageSegment.at)
Image = SegmentPattern("image", MessageSegment, MessageSegment.image)
Video = SegmentPattern("video", MessageSegment, MessageSegment.video)
File = SegmentPattern("file", MessageSegment, MessageSegment.file)
Audio = SegmentPattern("audio", MessageSegment, MessageSegment.audio)
KMarkdown = SegmentPattern("kmarkdown", MessageSegment, MessageSegment.kmarkdown)
Card = SegmentPattern("card", MessageSegment, MessageSegment.card)
Quote = SegmentPattern("quote", MessageSegment, MessageSegment.quote)
