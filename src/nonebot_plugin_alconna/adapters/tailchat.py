from warnings import warn

from nonebot_adapter_tailchat.message import MessageSegment

from nonebot_plugin_alconna.uniseg import Text
from nonebot_plugin_alconna.uniseg import Other
from nonebot_plugin_alconna.uniseg import At as UniAt
from nonebot_plugin_alconna.uniseg import File as UniFile
from nonebot_plugin_alconna.uniseg import Image as UniImage
from nonebot_plugin_alconna.typings import SegmentPattern, TextSegmentPattern

warn(
    "nonebot_plugin_alconna.adapters.tailchat is deprecated and will be removed in 0.57.0, "
    "please use nonebot_plugin_alconna.uniseg.segment instead.",
    DeprecationWarning,
    stacklevel=2,
)
At = SegmentPattern(
    "at",
    MessageSegment,
    UniAt,
    MessageSegment.at,
    additional=lambda x: x.flag == "user",
)
Panel = SegmentPattern(
    "url",
    MessageSegment,
    UniAt,
    MessageSegment.panel,
    additional=lambda x: x.flag == "channel",
)
Image = SegmentPattern("img", MessageSegment, UniImage, MessageSegment.img)
File = SegmentPattern("file", MessageSegment, UniFile, MessageSegment.file)
Emoji = SegmentPattern("emoji", MessageSegment, Other, MessageSegment.emoji)
Card = SegmentPattern("card", MessageSegment, Other, MessageSegment.card)


def link(self, x: Text):
    if x.extract_most_style() == "link":
        if not getattr(x, "_children", []):
            return MessageSegment.url(url=x.text)
        return MessageSegment.url(url=x.text, text=x._children[0].text)  # type: ignore
    return None


Url = TextSegmentPattern("url", MessageSegment, MessageSegment.url, link)


def markdown(self, x: Text):
    if x.extract_most_style() == "markdown":
        return MessageSegment.md(x.text)
    return None


Markdown = TextSegmentPattern("markdown", MessageSegment, MessageSegment.md, markdown)


def code(self, x: Text):
    if x.extract_most_style() == "code":
        return MessageSegment.code(x.text)
    return None


Code = TextSegmentPattern("code", MessageSegment, MessageSegment.code, code)
