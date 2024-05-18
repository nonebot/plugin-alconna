from nonebot_adapter_tailchat.message import MessageSegment

from nonebot_plugin_alconna.uniseg import Text
from nonebot_plugin_alconna.uniseg import Other
from nonebot_plugin_alconna.uniseg import At as UniAt
from nonebot_plugin_alconna.uniseg import File as UniFile
from nonebot_plugin_alconna.uniseg import Image as UniImage
from nonebot_plugin_alconna.typings import SegmentPattern, TextSegmentPattern

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
        else:
            return MessageSegment.url(url=x.text, text=x._children[0].text)  # type: ignore


Url = TextSegmentPattern("url", MessageSegment, MessageSegment.url, link)


def markdown(self, x: Text):
    if x.extract_most_style() == "markdown":
        return MessageSegment.md(x.text)


Markdown = TextSegmentPattern("markdown", MessageSegment, MessageSegment.md, markdown)


def code(self, x: Text):
    if x.extract_most_style() == "code":
        return MessageSegment.code(x.text)


Code = TextSegmentPattern("code", MessageSegment, MessageSegment.code, code)
