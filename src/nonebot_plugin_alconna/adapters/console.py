from nonebot.adapters.console.message import MessageSegment

from nonebot_plugin_alconna.uniseg import Text, Emoji
from nonebot_plugin_alconna.typings import SegmentPattern, TextSegmentPattern

Emoji = SegmentPattern("emoji", MessageSegment, Emoji, MessageSegment.emoji)


def markup(self, text: Text):
    if text.extract_most_style().startswith("markdown"):
        return MessageSegment.markup(text.text, style=text.extract_most_style().split(":")[1])


def markdown(self, text: Text):
    if text.extract_most_style().startswith("markdown"):
        return MessageSegment.markdown(text.text, code_theme=text.extract_most_style().split(":")[1])


Markup = TextSegmentPattern("markup", MessageSegment, MessageSegment.markup, markup)
Markdown = TextSegmentPattern("markdown", MessageSegment, MessageSegment.markdown, markdown)
