from nepattern.main import URL, INTEGER
from nonebot.adapters.satori.message import Message
from nonebot.adapters.satori.message import At as _At
from nonebot.adapters.satori.message import Br as _Br
from nonebot.adapters.satori.message import File as _File
from nonebot.adapters.satori.message import Link as _Link
from nonebot.adapters.satori.message import MessageSegment
from nonebot.adapters.satori.message import Audio as _Audio
from nonebot.adapters.satori.message import Image as _Image
from nonebot.adapters.satori.message import Sharp as _Sharp
from nonebot.adapters.satori.message import Video as _Video
from nepattern import BasePattern, PatternModel, UnionPattern
from nonebot.adapters.satori.message import Author as _Author
from nonebot.adapters.satori.message import Entity as _Entity
from nonebot.adapters.satori.message import Paragraph as _Paragraph
from nonebot.adapters.satori.message import RenderMessage as _RenderMessage

from nonebot_plugin_alconna.argv import MessageArgv
from nonebot_plugin_alconna.typings import SegmentPattern, TextSegmentPattern

Text = str
At = SegmentPattern("at", _At, MessageSegment.at)
AtRole = SegmentPattern("at", _At, MessageSegment.at_role)
Entity = SegmentPattern("entity", _Entity, MessageSegment.entity)
AtAll = SegmentPattern("at", _At, MessageSegment.at_all)
Sharp = SegmentPattern("sharp", _Sharp, MessageSegment.sharp)
Link = SegmentPattern("link", _Link, MessageSegment.link)
Image = SegmentPattern("img", _Image, MessageSegment.image)
Audio = SegmentPattern("audio", _Audio, MessageSegment.audio)
Video = SegmentPattern("video", _Video, MessageSegment.video)
File = SegmentPattern("file", _File, MessageSegment.file)
RenderMessage = SegmentPattern("message", _RenderMessage, MessageSegment.message)
Quote = SegmentPattern("quote", _RenderMessage, MessageSegment.quote)
Author = SegmentPattern("author", _Author, MessageSegment.author)

ImgOrUrl = (
    UnionPattern(
        [
            BasePattern(
                model=PatternModel.TYPE_CONVERT,
                origin=str,
                converter=lambda _, x: x.data["src"],
                alias="img",
                accepts=[Image],
            ),
            URL,
        ]
    )
    @ "img_url"
)
"""
内置类型, 允许传入图片元素(Image)或者链接(URL)，返回链接
"""

MentionID = (
    UnionPattern(
        [
            BasePattern(
                model=PatternModel.TYPE_CONVERT,
                origin=int,
                alias="at",
                accepts=[At],
                converter=lambda _, x: "id" in x.data and int(x.data["id"]),
            ),
            BasePattern(
                r"@(\d+)",
                model=PatternModel.REGEX_CONVERT,
                origin=int,
                alias="@xxx",
                accepts=[str],
                converter=lambda _, x: int(x[1]),
            ),
            INTEGER,
        ]
    )
    @ "at_id"
)
"""
内置类型，允许传入提醒元素(Mention)或者'@xxxx'式样的字符串或者数字, 返回数字
"""


def is_text(x: MessageSegment):
    return x.type in {"text", "br", "paragraph", "entity"}


styles = {
    "record": {},
    "index": 0,
    "msg": "",
}


def builder(self: MessageArgv, data: Message):
    styles["msg"] = str(data)
    _index = 0
    for index, unit in enumerate(data):
        if not self.is_text(unit):
            self.raw_data.append(unit)
            self.ndata += 1
            continue
        if unit.type == "br":
            unit.data["text"] = "\n"
        if not unit.data["text"].strip():
            if not index or index == len(data) - 1:
                continue
            if not self.is_text(data[index - 1]) or not self.is_text(data[index + 1]):
                continue
        text = unit.data["text"]
        if unit.type == "text":
            self.raw_data.append(text)
            self.ndata += 1
            continue
        if self.raw_data and self.raw_data[-1].__class__ is str:
            self.raw_data[-1] = f"{self.raw_data[-1]}{text}"
        else:
            self.raw_data.append(text)
            self.ndata += 1
        start = styles["msg"].find(text, _index)
        _index = start + len(text)
        styles["record"][(start, _index)] = unit.data["style"] if unit.type == "entity" else unit.type


def clean_style():
    styles["record"].clear()
    styles["index"] = 0


MessageArgv.custom_build(Message, is_text=is_text, builder=builder, cleanup=clean_style)


def locator(x: str, *t: str):
    start = styles["msg"].find(x, styles["index"])
    if start == -1:
        return False
    styles["index"] = start + len(x)
    if (maybe := styles["record"].get((start, styles["index"]))) and maybe in t:
        return True
    return any(
        scale[0] <= start <= scale[1]
        and scale[0] <= styles["index"] <= scale[1]
        and styles["record"][scale] in t
        for scale in styles["record"]
    )


Br = TextSegmentPattern("br", _Br, MessageSegment.br, locator=locator)
Paragraph = TextSegmentPattern("paragraph", _Paragraph, MessageSegment.paragraph, locator=locator)
Bold = TextSegmentPattern(
    "bold",
    _Entity,
    lambda m: MessageSegment.entity(m, "b"),
    lambda m, _: m.type == "entity",
    lambda m, _: locator(m, "b", "strong"),
)
Italic = TextSegmentPattern(
    "italic",
    _Entity,
    lambda m: MessageSegment.entity(m, "i"),
    lambda m, _: m.type == "entity",
    lambda m, _: locator(m, "i", "em"),
)
Underline = TextSegmentPattern(
    "underline",
    _Entity,
    lambda m: MessageSegment.entity(m, "u"),
    lambda m, _: m.type == "entity",
    lambda m, _: locator(m, "u", "ins"),
)
Strikethrough = TextSegmentPattern(
    "strikethrough",
    _Entity,
    lambda m: MessageSegment.entity(m, "s"),
    lambda m, _: m.type == "entity",
    lambda m, _: locator(m, "s", "del"),
)
Spoiler = TextSegmentPattern(
    "spoiler",
    _Entity,
    lambda m: MessageSegment.entity(m, "spl"),
    lambda m, _: m.type == "entity",
    lambda m, _: locator(m, "spl"),
)
Code = TextSegmentPattern(
    "code",
    _Entity,
    lambda m: MessageSegment.entity(m, "code"),
    lambda m, _: m.type == "entity",
    lambda m, _: locator(m, "code"),
)
Superscript = TextSegmentPattern(
    "superscript",
    _Entity,
    lambda m: MessageSegment.entity(m, "sup"),
    lambda m, _: m.type == "entity",
    lambda m, _: locator(m, "sup"),
)
Subscript = TextSegmentPattern(
    "subscript",
    _Entity,
    lambda m: MessageSegment.entity(m, "sub"),
    lambda m, _: m.type == "entity",
    lambda m, _: locator(m, "sub"),
)
