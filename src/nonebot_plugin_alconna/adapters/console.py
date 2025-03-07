from warnings import warn

from nonebot.adapters.console.message import MessageSegment

from nonebot_plugin_alconna.uniseg import Text, Emoji
from nonebot_plugin_alconna.typings import SegmentPattern, TextSegmentPattern

warn(
    "nonebot_plugin_alconna.adapters.console is deprecated and will be removed in 0.57.0, "
    "please use nonebot_plugin_alconna.uniseg.segment instead.",
    DeprecationWarning,
    stacklevel=2,
)
Emoji = SegmentPattern("emoji", MessageSegment, Emoji, MessageSegment.emoji)


def markup(self, text: Text):
    if text.extract_most_style().startswith("markdown"):
        return MessageSegment.markup(text.text, style=text.extract_most_style().split(":")[1])
    return None


def markdown(self, text: Text):
    if text.extract_most_style().startswith("markdown"):
        return MessageSegment.markdown(text.text, code_theme=text.extract_most_style().split(":")[1])
    return None


Markup = TextSegmentPattern("markup", MessageSegment, MessageSegment.markup, markup)
Markdown = TextSegmentPattern("markdown", MessageSegment, MessageSegment.markdown, markdown)
