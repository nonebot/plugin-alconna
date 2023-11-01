from nepattern.main import URL, INTEGER
from nonebot.adapters.satori.message import Message
from nonebot.adapters.satori.message import At as _At
from nonebot.adapters.satori.message import Br as _Br
from nonebot.adapters.satori.message import Bold as _Bold
from nonebot.adapters.satori.message import Code as _Code
from nonebot.adapters.satori.message import File as _File
from nonebot.adapters.satori.message import Link as _Link
from nonebot.adapters.satori.message import MessageSegment
from nonebot.adapters.satori.message import Audio as _Audio
from nonebot.adapters.satori.message import Image as _Image
from nonebot.adapters.satori.message import Sharp as _Sharp
from nonebot.adapters.satori.message import Video as _Video
from nepattern import BasePattern, PatternModel, UnionPattern
from nonebot.adapters.satori.message import Author as _Author
from nonebot.adapters.satori.message import Italic as _Italic
from nonebot.adapters.satori.message import Spoiler as _Spoiler
from nonebot.adapters.satori.message import Paragraph as _Paragraph
from nonebot.adapters.satori.message import Subscript as _Subscript
from nonebot.adapters.satori.message import Underline as _Underline
from nonebot.adapters.satori.message import Superscript as _Superscript
from nonebot.adapters.satori.message import RenderMessage as _RenderMessage
from nonebot.adapters.satori.message import Strikethrough as _Strikethrough

from nonebot_plugin_alconna.argv import MessageArgv
from nonebot_plugin_alconna.typings import SegmentPattern, TextSegmentPattern

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
        styles["record"][(start, _index)] = unit.type


def clean_style():
    styles["record"].clear()
    styles["index"] = 0


MessageArgv.custom_build(Message, builder=builder, cleanup=clean_style)


def locator(x: str, t: str):
    start = styles["msg"].find(x, styles["index"])
    if start == -1:
        return False
    styles["index"] = start + len(x)
    if (maybe := styles["record"].get((start, styles["index"]))) and maybe == t:
        return True
    return any(
        scale[0] <= start <= scale[1]
        and scale[0] <= styles["index"] <= scale[1]
        and styles["record"][scale] == t
        for scale in styles["record"]
    )


Br = TextSegmentPattern("br", _Br, MessageSegment.br, locator)
Paragraph = TextSegmentPattern("paragraph", _Paragraph, MessageSegment.paragraph, locator)
Bold = TextSegmentPattern("bold", _Bold, MessageSegment.bold, locator)
Italic = TextSegmentPattern("italic", _Italic, MessageSegment.italic, locator)
Underline = TextSegmentPattern("underline", _Underline, MessageSegment.underline, locator)
Strikethrough = TextSegmentPattern("strikethrough", _Strikethrough, MessageSegment.strikethrough, locator)
Spoiler = TextSegmentPattern("spoiler", _Spoiler, MessageSegment.spoiler, locator)
Code = TextSegmentPattern("code", _Code, MessageSegment.code, locator)
Superscript = TextSegmentPattern("superscript", _Superscript, MessageSegment.superscript, locator)
Subscript = TextSegmentPattern("subscript", _Subscript, MessageSegment.subscript, locator)
