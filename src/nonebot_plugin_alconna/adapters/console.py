from nonebot_plugin_alconna.typings import SegmentPattern
from nonebot.adapters.console.message import MessageSegment
from nonebot.adapters.console.message import Emoji as _Emoji
from nonebot.adapters.console.message import Markup as _Markup
from nonebot.adapters.console.message import Markdown as _Markdown
from nonebot_plugin_alconna.argv import MessageArgv
from arclet.alconna import set_default_argv_type

set_default_argv_type(MessageArgv)

Emoji = SegmentPattern("emoji", _Emoji, MessageSegment.emoji)
Markup = SegmentPattern("markup", _Markup, MessageSegment.markup)
Markdown = SegmentPattern("markdown", _Markdown, MessageSegment.markdown)

Text = str
