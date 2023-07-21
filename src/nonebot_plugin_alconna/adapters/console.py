from nonebot.adapters.console.message import Message
from nonebot.adapters.console.message import Emoji as _Emoji
from arclet.alconna import argv_config, set_default_argv_type
from nonebot.adapters.console.message import Markup as _Markup
from nonebot.adapters.console.message import Markdown as _Markdown
from nonebot.adapters.console.message import BaseMessage, MessageSegment

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

Emoji = SegmentPattern("emoji", _Emoji, MessageSegment.emoji)
Markup = SegmentPattern("markup", _Markup, MessageSegment.markup)
Markdown = SegmentPattern("markdown", _Markdown, MessageSegment.markdown)

Text = str
