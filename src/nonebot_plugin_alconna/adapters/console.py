from nonebot.adapters import Message as BaseMessage
from arclet.alconna import argv_config, set_default_argv_type
from nonebot.adapters.console.message import Message, MessageSegment

from nonebot_plugin_alconna.argv import MessageArgv
from nonebot_plugin_alconna.typings import SegmentPattern


class ConsoleMessageArgv(MessageArgv):
    ...


set_default_argv_type(ConsoleMessageArgv)
argv_config(
    ConsoleMessageArgv,
    filter_out=[],
    checker=lambda x: isinstance(x, BaseMessage),
    to_text=lambda x: x if x.__class__ is str else str(x) if x.is_text() else None,
    converter=lambda x: Message(x),
)

Emoji = SegmentPattern("emoji", MessageSegment, MessageSegment.emoji)
Markup = SegmentPattern("markup", MessageSegment, MessageSegment.markup)
Markdown = SegmentPattern("markdown", MessageSegment, MessageSegment.markdown)

Text = str
