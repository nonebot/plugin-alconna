from warnings import warn

from nonebot.adapters.mail.message import MessageSegment

from nonebot_plugin_alconna.uniseg.segment import Text, Media
from nonebot_plugin_alconna.typings import SegmentPattern, TextSegmentPattern

warn(
    "nonebot_plugin_alconna.adapters.mail is deprecated and will be removed in 0.57.0, "
    "please use nonebot_plugin_alconna.uniseg.segment instead.",
    DeprecationWarning,
    stacklevel=2,
)
Attachment = SegmentPattern("attachment", MessageSegment, Media, MessageSegment.attachment)


def is_html(self, text: Text):
    if text.extract_most_style().startswith("html"):
        return MessageSegment.html(text.text)
    return None


Markup = TextSegmentPattern("html", MessageSegment, MessageSegment.html, is_html)
