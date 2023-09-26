from nonebot.adapters.console.message import MessageSegment

from nonebot_plugin_alconna.typings import SegmentPattern

Emoji = SegmentPattern("emoji", MessageSegment, MessageSegment.emoji)
Markup = SegmentPattern("markup", MessageSegment, MessageSegment.markup)
Markdown = SegmentPattern("markdown", MessageSegment, MessageSegment.markdown)

Text = str
