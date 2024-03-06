from typing import Union, TYPE_CHECKING

from nepattern.base import URL, INTEGER
from nonebot.adapters import Message as BaseMessage
from nonebot.adapters.satori.message import Message
from nonebot.adapters.satori.message import At as _At
from nonebot.adapters.satori.message import Br as _Br
from nonebot.adapters.satori.message import Text as _Text
from nonebot.adapters.satori.message import File as _File
from nonebot.adapters.satori.message import Link as _Link
from nepattern import MatchMode, BasePattern, UnionPattern
from nonebot.adapters.satori.message import MessageSegment
from nonebot.adapters.satori.message import Audio as _Audio
from nonebot.adapters.satori.message import Image as _Image
from nonebot.adapters.satori.message import Sharp as _Sharp
from nonebot.adapters.satori.message import Video as _Video
from nonebot.adapters.satori.message import Author as _Author
from nonebot.adapters.satori.message import RenderMessage as _RenderMessage

from nonebot_plugin_alconna.argv import MessageArgv
from nonebot_plugin_alconna.typings import SegmentPattern, StyleTextPattern

Text = str
At = SegmentPattern("at", _At, MessageSegment.at, lambda x: "id" in x.data)
AtRole = SegmentPattern("at", _At, MessageSegment.at_role, lambda x: "role" in x.data)
AtAll = SegmentPattern("at", _At, MessageSegment.at_all, lambda x: x.data.get("type") in ("all", "here"))
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
                mode=MatchMode.TYPE_CONVERT,
                origin=str,
                converter=lambda _, x: x.data["src"],
                alias="img",
                addition_accepts=Image,
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
    UnionPattern[Union[str, _At]](
        [
            BasePattern(
                mode=MatchMode.TYPE_CONVERT,
                origin=int,
                alias="at",
                addition_accepts=At,
                converter=lambda _, x: "id" in x.data and int(x.data["id"]),
            ),
            BasePattern(
                r"@(\d+)",
                mode=MatchMode.REGEX_CONVERT,
                origin=int,
                alias="@xxx",
                accepts=str,
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


styles = {
    "record": {},
    "index": 0,
    "msg": "",
}


def builder(self: MessageArgv, data: Message):
    styles["msg"] = data.extract_plain_text()
    _index = 0
    for index, unit in enumerate(data):
        if not self.is_text(unit):
            self.raw_data.append(unit)
            self.ndata += 1
            continue
        if not unit.data["text"].strip():
            if not index or index == len(data) - 1:
                continue
            if not self.is_text(data[index - 1]) or not self.is_text(data[index + 1]):
                continue
        if TYPE_CHECKING:
            assert isinstance(unit, _Text)
        text = unit.data["text"]
        if not (_styles := unit.data.get("styles")):
            self.raw_data.append(text)
            self.ndata += 1
            continue
        if self.raw_data and self.raw_data[-1].__class__ is str:
            self.raw_data[-1] = f"{self.raw_data[-1]}{text}"
        else:
            self.raw_data.append(text)
            self.ndata += 1

        start = styles["msg"].find(text, _index)
        for scale, style in _styles.items():
            styles["record"][(start + scale[0], start + scale[1])] = style


def clean_style():
    styles["record"].clear()
    styles["index"] = 0


MessageArgv.custom_build(Message, builder=builder, cleanup=clean_style)


def locator(x: str, expected: list[str]):
    start = styles["msg"].find(x, styles["index"])
    if start == -1:
        return
    styles["index"] = start + len(x)
    if (maybe := styles["record"].get((start, styles["index"]))) and set(maybe).issuperset(expected):
        return _Text("text", {"text": x, "styles": {(0, len(x)): maybe}})
    _styles = {}
    _len = len(x)
    for scale, style in styles["record"].items():
        if start <= scale[0] < styles["index"] <= scale[1]:
            _styles[(scale[0] - start, scale[1] - start)] = style
        if scale[0] <= start <= scale[1] <= styles["index"]:
            _styles[(0, scale[1] - start)] = style
        if start <= scale[0] < scale[1] <= styles["index"]:
            _styles[(scale[0] - start, scale[1] - start)] = style
        if scale[0] <= start < styles["index"] <= scale[1]:
            _styles[(scale[0] - start, _len)] = style
    if all(set(style).issuperset(expected) for style in _styles.values()):
        return _Text("text", {"text": x, "styles": _styles})
    return



Paragraph = StyleTextPattern("p", _Text, MessageSegment.paragraph, locator)
Bold = StyleTextPattern("b", _Text, MessageSegment.bold, locator)
Italic = StyleTextPattern("i", _Text, MessageSegment.italic, locator)
Underline = StyleTextPattern("u", _Text, MessageSegment.underline, locator)
Strikethrough = StyleTextPattern("s", _Text, MessageSegment.strikethrough, locator)
Spoiler = StyleTextPattern("spl", _Text, MessageSegment.spoiler, locator)
Code = StyleTextPattern("code", _Text, MessageSegment.code, locator)
Superscript = StyleTextPattern("sup", _Text, MessageSegment.superscript, locator)
Subscript = StyleTextPattern("sub", _Text, MessageSegment.subscript, locator)
