from nonebot.adapters.mail.message import MessageSegment

from nonebot_plugin_alconna.uniseg.segment import Text, Media
from nonebot_plugin_alconna.typings import SegmentPattern, TextSegmentPattern

Attachment = SegmentPattern("attachment", MessageSegment, Media, MessageSegment.attachment)


def is_html(self, text: Text):
    if text.extract_most_style().startswith("html"):
        return MessageSegment.html(text.text)


Markup = TextSegmentPattern("html", MessageSegment, MessageSegment.html, is_html)
