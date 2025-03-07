"""通用标注, 无法用于创建 MS对象"""

import re
import json
import base64
import hashlib
import importlib
import contextlib
from io import BytesIO
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
from typing_extensions import Self
from functools import reduce, lru_cache
from collections.abc import Iterable, Awaitable
from dataclasses import InitVar, field, asdict, fields, dataclass
from typing import TYPE_CHECKING, Any, Union, Literal, TypeVar, Callable, ClassVar, Optional, Protocol, overload

from nonebot import require
from tarina import gen_subclass
from tarina.lang.model import LangItem
from nonebot.compat import custom_validation
from nonebot.internal.adapter import Bot, Message, MessageSegment
from nepattern import MatchMode, BasePattern, create_local_patterns

from .utils import fleep
from .constraint import lang
from .fallback import FallbackStrategy

if TYPE_CHECKING:
    from .message import UniMessage
    from .builder import MessageBuilder
    from .exporter import MessageExporter


TS = TypeVar("TS", bound="Segment")
TS1 = TypeVar("TS1", bound="Segment")


@lru_cache(4096)
def get_segment_class(name: str) -> type["Segment"]:
    return next((cls for cls in gen_subclass(Segment) if cls.__name__.lower() == name), Segment)


@custom_validation
@dataclass
class Segment:
    """基类标注"""

    origin: Optional[MessageSegment] = field(init=False, hash=False, repr=False, compare=False, default=None)
    _children: list["Segment"] = field(init=False, default_factory=list, repr=False, hash=False)

    def __str__(self):
        return f"[{self.__class__.__name__.lower()}]"

    @overload
    def __add__(self: TS, item: str) -> "UniMessage[Union[TS, Text]]": ...

    @overload
    def __add__(self: TS, item: Union[TS, Iterable[TS]]) -> "UniMessage[TS]": ...

    @overload
    def __add__(self: TS, item: Union[TS1, Iterable[TS1]]) -> "UniMessage[Union[TS, TS1]]": ...

    def __add__(self: TS, item: Union[str, Union[TS, TS1], Iterable[Union[TS, TS1]]]) -> "UniMessage":
        from .message import UniMessage

        return UniMessage(self) + item

    @overload
    def __radd__(self: TS, item: str) -> "UniMessage[Union[Text, TS]]": ...

    @overload
    def __radd__(self: TS, item: Union[TS, Iterable[TS]]) -> "UniMessage[TS]": ...

    @overload
    def __radd__(self: TS, item: Union[TS1, Iterable[TS1]]) -> "UniMessage[Union[TS1, TS]]": ...

    def __radd__(self: TS, item: Union[str, Union[TS, TS1], Iterable[Union[TS, TS1]]]) -> "UniMessage":
        from .message import UniMessage

        return UniMessage(item) + self

    def is_text(self) -> bool:
        return False

    @property
    def type(self) -> str:
        return self.__class__.__name__.lower()

    @property
    def data(self) -> dict[str, Any]:
        res = asdict(self)
        res.pop("origin", None)
        res.pop("_children", None)
        return res

    def __call__(self, *segments: Union[str, "TS"]) -> Self:
        if not segments:
            return self
        self._children.extend(Text(s) if isinstance(s, str) else s for s in segments)
        return self

    @property
    def children(self):
        return self._children

    @classmethod
    def __get_validators__(cls):
        yield cls._validate

    @classmethod
    def _validate(cls, value) -> Self:
        if isinstance(value, cls):
            return value
        raise ValueError(f"Type {type(value)} can not be converted to {cls}")

    def dump(self, *, media_save_dir: Optional[Union[str, Path, bool]] = None) -> dict:
        """将对象转为 dict 数据
        注意：
            若 media_save_dir 为 False，则不会保存媒体文件。
            若 media_save_dir 为 True，则会将文件数据转为 base64 编码。
            若不指定 media_save_dir，则会尝试导入 `nonebot_plugin_localstore` 并使用其提供的路径。
            否则，将会尝试使用当前工作目录。
        """
        data = {f.name: getattr(self, f.name) for f in fields(self) if f.name not in ("origin", "_children")}
        data = {"type": self.type, **{k: v for k, v in data.items() if v is not None}}
        if isinstance(self, Media):
            if self.name == self.__default_name__:
                data.pop("name", None)
            if self.url or self.path or not self.raw:
                data.pop("raw", None)
                data.pop("mimetype", None)
            elif media_save_dir is True:
                data["raw"] = base64.b64encode(self.raw_bytes).decode()
            elif media_save_dir is not False:
                path = self.save(media_save_dir=media_save_dir)
                del data["raw"]
                del data["mimetype"]
                data["path"] = str(path.resolve().as_posix())
        if self._children:
            data["children"] = [child.dump(media_save_dir=media_save_dir) for child in self._children]
        return data

    @classmethod
    def load(cls, data: dict) -> Self:
        if children := data.get("children", []):
            children = [get_segment_class(child["type"]).load(child) for child in children]
        return cls(**{k: v for k, v in data.items() if k not in ("type", "children")})(*children)  # type: ignore


STYLE_TYPE_MAP = {
    "reset": "0",
    "bold": "1",
    "highlight": "1",
    "strong": "1",
    "bright": "1",
    "dim": "2",
    "thin": "2",
    "italic": "3",
    "underline": "4",
    "flash": "5",
    "blink": "5",
    "rapid": "6",
    "sparkle": "5",
    "code": "7",
    "inverse": "7",
    "spoiler": "8",
    "invisible": "8",
    "strikethrough": "9",
    "delete": "9",
    "cross": "9",
    "black": "30",
    "red": "31",
    "green": "32",
    "yellow": "33",
    "gold": "33",
    "blue": "34",
    "purple": "35",
    "magenta": "35",
    "cyan": "36",
    "aqua": "36",
    "gray": "37",
    "white": "37",
    "default": "39",
    "bg_black": "40",
    "bg_red": "41",
    "bg_green": "42",
    "bg_yellow": "43",
    "bg_gold": "43",
    "bg_blue": "44",
    "bg_purple": "45",
    "bg_cyan": "46",
    "bg_aqua": "46",
    "bg_white": "47",
    "obfuscated": "47",
    "bg_default": "49",
    "dark_gray": "90",
    "light_black": "90",
    "light_red": "91",
    "light_green": "92",
    "light_yellow": "93",
    "light_gold": "93",
    "light_blue": "94",
    "light_purple": "95",
    "light_magenta": "95",
    "light_aqua": "96",
    "light_cyan": "96",
    "light_white": "97",
    "link": "96;4",
    "bg_light_black": "100",
    "bg_light_red": "101",
    "bg_light_green": "102",
    "bg_light_yellow": "103",
    "bg_light_gold": "103",
    "bg_light_blue": "104",
    "bg_light_purple": "105",
    "bg_light_cyan": "106",
    "bg_light_aqua": "106",
    "bg_light_white": "107",
}


@dataclass
class Text(Segment):
    """Text对象, 表示一类文本元素"""

    text: str
    styles: dict[tuple[int, int], list[str]] = field(default_factory=dict)

    def __post_init__(self):
        self.text = str(self.text)

    def is_text(self) -> bool:
        return True

    def __merge__(self):
        data = {}
        styles = self.styles
        if not styles:
            return
        for scale, _styles in styles.items():
            for i in range(*scale):
                if i not in data:
                    data[i] = _styles[:]
                else:
                    data[i].extend(s for s in _styles if s not in data[i])
        styles.clear()
        data1: dict[str, list] = {}
        for i, _styles in data.items():
            key = "\x01".join(_styles)
            data1.setdefault(key, []).append(i)
        data.clear()
        for key, indexes in data1.items():
            start = indexes[0]
            end = start
            for i in indexes[1:]:
                if i - end == 1:
                    end = i
                else:
                    data[(start, end + 1)] = key.split("\x01")
                    start = end = i
            if end >= start:
                data[(start, end + 1)] = key.split("\x01")
        for scale in sorted(data.keys()):
            styles[scale] = data[scale]

    def cover(self, text: str):
        self._children = [Text(text)]
        return self

    def mark(self, start: Optional[int] = None, end: Optional[int] = None, *styles: str):
        if start is None:
            start = 0
        elif start < 0:
            start += len(self.text)
        if end is None:
            end = len(self.text)
        elif end < 0:
            end += len(self.text)
        if not styles:
            return self
        _styles = self.styles.setdefault((start, end), [])
        for sty in styles:
            if sty not in _styles:
                _styles.append(sty)
        self.__merge__()
        return self

    def bold(self, start: Optional[int] = None, end: Optional[int] = None):
        return self.mark(start, end, "bold")

    def italic(self, start: Optional[int] = None, end: Optional[int] = None):
        return self.mark(start, end, "italic")

    def underline(self, start: Optional[int] = None, end: Optional[int] = None):
        return self.mark(start, end, "underline")

    def strikethrough(self, start: Optional[int] = None, end: Optional[int] = None):
        return self.mark(start, end, "strikethrough")

    def spoiler(self, start: Optional[int] = None, end: Optional[int] = None):
        return self.mark(start, end, "spoiler")

    def link(self, start: Optional[int] = None, end: Optional[int] = None):
        return self.mark(start, end, "link")

    def code(self, start: Optional[int] = None, end: Optional[int] = None):
        return self.mark(start, end, "code")

    def markdown(self, start: Optional[int] = None, end: Optional[int] = None):
        return self.mark(start, end, "markdown")

    def color(self, color: str, start: Optional[int] = None, end: Optional[int] = None):
        if color not in STYLE_TYPE_MAP:
            raise ValueError(f"Color {color} is not supported")
        return self.mark(start, end, color)

    def __str__(self) -> str:
        result = []
        text = self.text
        styles = self.styles
        if not styles:
            return text
        self.__merge__()
        scales = sorted(styles.keys(), key=lambda x: x[0])
        left = scales[0][0]
        result.append(text[:left])
        for scale in scales:
            prefix = "".join(f"<{style}>" for style in styles[scale])
            suffix = "".join(f"</{style}>" for style in reversed(styles[scale]))
            result.append(prefix + text[scale[0] : scale[1]] + suffix)
        right = scales[-1][1]
        result.append(text[right:])
        text = "".join(result)
        pat = re.compile(r"</(\w+)(?<!/p)><\1>")
        for _ in range(max(map(len, styles.values()))):
            text = pat.sub("", text)
        return text

    def __rich__(self):
        result = []
        text = self.text
        styles = self.styles
        if not styles:
            return text
        self.__merge__()
        scales = sorted(styles.keys(), key=lambda x: x[0])
        left = scales[0][0]
        result.append(text[:left])
        for scale in scales:
            prefix = ";".join(f"{STYLE_TYPE_MAP[style]}" for style in styles[scale])
            result.append(f"\033[{prefix}m{text[scale[0] : scale[1]]}\033[0m")
        right = scales[-1][1]
        result.append(text[right:])
        return "".join(result)

    def extract_most_style(self) -> str:
        if not self.styles:
            return ""
        max_scale = max(self.styles, key=lambda x: x[1] - x[0], default=(0, 0))
        return self.styles[max_scale][0]

    def extract_most_styles(self) -> list[str]:
        if not self.styles:
            return []
        max_scale = max(self.styles, key=lambda x: x[1] - x[0], default=(0, 0))
        return self.styles[max_scale]

    def style_split(self):
        result: list[Text] = []
        text = self.text
        styles = self.styles
        if not styles:
            return [self]
        self.__merge__()
        scales = sorted(styles.keys(), key=lambda x: x[0])
        left = scales[0][0]
        if left > 0:
            result.append(Text(text[:left]))
        for scale in scales:
            result.append(Text(text[scale[0] : scale[1]], {(scale[0] - left, scale[1] - left): styles[scale]}))
            left = scale[0]
        right = scales[-1][1]
        if right < len(text):
            result.append(Text(text[right:]))
        return result

    def _merge_text(self, other: "Text"):
        _len = len(self.text)
        if not other.text:
            return self
        self.text += other.text
        for scale, styles in other.styles.items():
            self.styles[(scale[0] + _len, scale[1] + _len)] = styles[:]
        self.__merge__()
        return self

    @overload
    def __add__(self, item: Union[str, "Text"]) -> "Text": ...
    @overload
    def __add__(self, item: Union[TS1, Iterable[TS1]]) -> "UniMessage[Union[Text, TS1]]": ...

    def __add__(self, item: Union[str, Union["Text", TS1], Iterable[TS1]]):
        from .message import UniMessage

        if isinstance(item, str):
            return Text(self.text + item, self.styles)

        if isinstance(item, Text):
            new = Text(self.text, self.styles)
            return new._merge_text(item)

        return UniMessage(Text(self.text, self.styles)) + item

    @overload
    def __radd__(self, item: Union[str, "Text"]) -> "Text": ...

    @overload
    def __radd__(self, item: Union[TS1, Iterable[TS1]]) -> "UniMessage[Union[TS1, Text]]": ...

    def __radd__(self, item: Union[str, Union["Text", TS1], Iterable[TS1]]):
        from .message import UniMessage

        if isinstance(item, str):
            return Text(item)._merge_text(self)

        if isinstance(item, Text):
            new = Text(item.text, item.styles)
            return new._merge_text(self)

        return UniMessage(item) + Text(self.text, self.styles)

    @overload
    def __getitem__(self, item: int) -> str: ...

    @overload
    def __getitem__(self, item: slice) -> "Text": ...

    def __getitem__(self, item: Union[int, slice]):
        if isinstance(item, int):
            return self.text[item]
        start = item.start or 0
        end = item.stop or len(self.text)
        if end < 0:
            end += len(self.text)
        text = self.text[item]
        len_ = len(text)
        res = Text(
            text,
            {
                (max(_start - start, 0), min(_end - start, len_)): style
                for (_start, _end), style in self.styles.items()
                if _start < end and _end > start
            },
        )
        res.__merge__()
        return res

    def split(self, pattern: Optional[str] = None):
        parts = self.text.split(pattern)
        if len(parts) == 1:
            return [Text(self.text, self.styles)]
        styles = self.styles
        text = self.text
        index = 0
        result: list[Text] = []
        for part in parts:
            start = text.find(part, index)
            if start == -1:
                result.append(Text(part))
                continue
            index = start + len(part)
            if maybe := styles.get((start, index)):
                result.append(Text(part, {(0, len(part)): maybe}))
                continue
            _styles = {}
            for scale, style in styles.items():
                if start <= scale[0] < index <= scale[1]:
                    _styles[(scale[0] - start, index - start)] = style
                elif scale[0] <= start < scale[1] <= index:
                    _styles[(0, scale[1] - start)] = style
                elif start <= scale[0] < scale[1] <= index:
                    _styles[(scale[0] - start, scale[1] - start)] = style
                elif scale[0] <= start < index <= scale[1]:
                    _styles[(0, index - start)] = style
            result.append(Text(part, _styles))
        return result

    def replace(self, old: str, new: Union[str, "Text"]) -> "Text":
        text = self.text
        index = 0
        new_text = new if isinstance(new, str) else new.text
        old_len = len(old)
        start = text.find(old, index)
        if start == -1:
            return self
        texts = [self[:start]]
        old_t = self[start : start + old_len]
        texts.append(
            Text(new_text).mark(None, None, *old_t.style_split()[0].extract_most_styles())
            if isinstance(new, str)
            else new
        )
        index = start + old_len
        while (start := text.find(old, index)) != -1:
            if start > index:
                texts.append(self[index:start])
            old_t = self[start : start + old_len]
            texts.append(
                Text(new_text).mark(None, None, *old_t.style_split()[0].extract_most_styles())
                if isinstance(new, str)
                else new
            )
            index = start + old_len
        if index < len(text):
            texts.append(self[index:])
        return reduce(lambda x, y: x + y, texts)

    def lstrip(self, chars: Optional[str] = None) -> "Text":
        text = self.text
        changed = self.text.lstrip(chars)
        if changed == text:
            return self
        return self[len(text) - len(changed) :]

    def rstrip(self, chars: Optional[str] = None) -> "Text":
        text = self.text
        changed = self.text.rstrip(chars)
        if changed == text:
            return self
        return self[: len(changed)]

    def strip(self, chars: str = " ") -> "Text":
        return self.lstrip(chars).rstrip(chars)

    def dump(self, **kwargs) -> dict:
        data: dict = {"type": "text", "text": self.text}
        if self.styles:
            data["styles"] = {":".join(map(str, k)): v for k, v in self.styles.items()}
        return data

    @classmethod
    def load(cls, data: dict) -> "Text":
        styles = {}
        if "styles" in data:
            for k, v in data["styles"].items():
                styles[tuple(map(int, k.split(":")))] = v
        return cls(data["text"], styles)


@dataclass
class At(Segment):
    """At对象, 表示一类提醒某用户的元素"""

    flag: Literal["user", "role", "channel"]
    target: str
    display: Optional[str] = field(default=None)


@dataclass
class AtAll(Segment):
    """AtAll对象, 表示一类提醒所有人的元素"""

    here: bool = field(default=False)


@dataclass
class Emoji(Segment):
    """Emoji对象, 表示一类表情元素"""

    id: str
    name: Optional[str] = field(default=None)


class MediaToUrl(Protocol):
    def __call__(
        self, data: Union[str, Path, bytes, BytesIO], bot: Optional[Bot], name: Optional[str] = None
    ) -> Awaitable[str]: ...


@dataclass
class Media(Segment):
    id: Optional[str] = field(default=None)
    url: Optional[str] = field(default=None)
    path: Optional[Union[str, Path]] = field(default=None)
    raw: Optional[Union[bytes, BytesIO]] = field(default=None)
    mimetype: Optional[str] = field(default=None)
    name: str = field(default="media")

    __default_name__ = "media"
    to_url: ClassVar[Optional[MediaToUrl]] = None

    def __is_default_name(self) -> bool:
        return self.name == self.__default_name__

    def __post_init__(self):
        if self.path and self.__is_default_name():
            self.name = Path(self.path).name
        if self.url and not urlparse(self.url).hostname:
            self.url = f"https://{self.url}"

    @property
    def raw_bytes(self) -> bytes:
        if not self.raw:
            raise ValueError(f"{self} has no raw data")
        raw = self.raw.getvalue() if isinstance(self.raw, BytesIO) else self.raw
        if (not self.mimetype) or self.__is_default_name():
            header = raw[:128]
            info = fleep.get(header)
            if not self.mimetype:
                self.mimetype = info.mimes[0] if info.mimes else self.mimetype
            if self.__is_default_name() and info.types and info.extensions:
                self.name = f"{info.types[0]}.{info.extensions[0]}"
        return raw

    @classmethod
    def load(cls, data: dict) -> Self:
        if children := data.get("children", []):
            children = [get_segment_class(child["type"]).load(child) for child in children]
        if "raw" in data and isinstance(data["raw"], str):
            data["raw"] = base64.b64decode(data["raw"])
        return cls(**{k: v for k, v in data.items() if k not in ("type", "children")})(*children)  # type: ignore

    def save(self, media_save_dir: Optional[Union[str, Path]] = None) -> Path:
        if not self.raw:
            raise ValueError
        if isinstance(media_save_dir, (str, Path)):
            dir_ = Path(media_save_dir)
        else:
            try:
                require("nonebot_plugin_localstore")
                from nonebot_plugin_localstore import get_data_dir

                dir_ = get_data_dir("nonebot_plugin_alconna") / "media"
            except ImportError:
                get_data_dir = None
                dir_ = Path.cwd() / ".data" / "media"
        raw = self.raw.getvalue() if isinstance(self.raw, BytesIO) else self.raw
        header = raw[:128]
        info = fleep.get(header)
        ext = info.extensions[0] if info.extensions else "bin"
        md5 = hashlib.md5(raw).hexdigest()
        path = dir_ / md5[:2] / f"{md5}.{ext}"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb+") as f:
            f.write(raw)
        return path.resolve()


@dataclass
class Image(Media):
    """Image对象, 表示一类图片元素"""

    width: Optional[int] = field(default=None)
    height: Optional[int] = field(default=None)
    name: str = field(default="image.png")

    __default_name__ = "image.png"


@dataclass
class Audio(Media):
    """Audio对象, 表示一类音频元素"""

    duration: Optional[float] = field(default=None)
    name: str = field(default="audio.mp3")

    __default_name__ = "audio.mp3"


@dataclass
class Voice(Media):
    """Voice对象, 表示一类语音元素"""

    duration: Optional[float] = field(default=None)
    name: str = field(default="voice.wav")

    __default_name__ = "voice.wav"


@dataclass
class Video(Media):
    """Video对象, 表示一类视频元素"""

    thumbnail: Optional[Image] = field(default=None)
    name: str = field(default="video.mp4")

    __default_name__ = "video.mp4"


@dataclass
class File(Media):
    """File对象, 表示一类文件元素"""

    name: str = field(default="file.bin")

    __default_name__ = "file.bin"


@dataclass(init=False)
class Reply(Segment):
    """Reply对象，表示一类回复消息"""

    id: str
    """此处不一定是消息ID，可能是其他ID，如消息序号等"""
    msg: Optional[Union[Message, str]]
    origin: Optional[Any]

    def __init__(
        self,
        id: str,
        msg: Optional[Union[Message, str]] = None,
        origin: Optional[Any] = None,
    ):
        self.id = id
        self.msg = msg
        self.origin = origin
        if not hasattr(self, "_children"):
            self._children = []

    def dump(self, *, media_save_dir: Optional[Union[str, Path, bool]] = None) -> dict:
        data = super().dump(media_save_dir=media_save_dir)
        data["id"] = self.id
        data.pop("msg", None)
        return data


@dataclass
class RefNode:
    """表示转发消息的引用消息元素"""

    id: str
    """消息id"""
    context: Optional[str] = None
    """可能的群聊id"""

    def dump(self, **kwargs):
        return {"type": "ref", "id": self.id, "context": self.context}

    @classmethod
    def load(cls, data: dict):
        return cls(data["id"], data.get("context"))


@dataclass
class CustomNode:
    """表示转发消息的自定义消息元素"""

    uid: str
    """消息发送者id"""
    name: str
    """消息发送者昵称"""
    content: Union[str, "UniMessage", list[Segment]]
    """消息内容"""
    time: datetime = field(default_factory=datetime.now)
    """消息发送时间"""
    context: Optional[str] = None
    """可能的群聊id"""

    def dump(self, *, media_save_dir: Optional[Union[str, Path, bool]] = None):
        return {
            "type": "custom",
            "uid": self.uid,
            "name": self.name,
            "content": (
                self.content
                if isinstance(self.content, str)
                else [seg.dump(media_save_dir=media_save_dir) for seg in self.content]
            ),
            "time": self.time.timestamp(),
            "context": self.context,
        }

    @classmethod
    def load(cls, data: dict):
        if isinstance(data["content"], str):
            content = data["content"]
        else:
            content = [get_segment_class(seg["type"]).load(seg) for seg in data["content"]]
        return cls(
            data["uid"], data["name"], content, datetime.fromtimestamp(data["time"]), data["context"]  # noqa: DTZ006
        )


@dataclass
class Reference(Segment):
    """Reference对象，表示一类引用消息。转发消息 (Forward) 也属于此类"""

    id: Optional[str] = field(default=None)
    """此处不一定是消息ID，可能是其他ID，如消息序号等"""
    nodes: InitVar[Union[list[RefNode], list[CustomNode], list[Union[RefNode, CustomNode]], None]] = field(default=None)
    _children: list[Union[RefNode, CustomNode]] = field(init=False, default_factory=list)

    def __post_init__(self, nodes: Union[list[RefNode], list[CustomNode], list[Union[RefNode, CustomNode]], None]):
        if nodes:
            self._children.extend(nodes)

    @property
    def children(self):
        return self._children

    def __call__(self, *segments: Union[Segment, RefNode, CustomNode]) -> Self:
        if not segments:
            return self
        self._children.extend(segments)  # type: ignore
        return self

    def dump(self, *, media_save_dir: Optional[Union[str, Path, bool]] = None) -> dict:
        return {
            "type": self.type,
            "id": self.id,
            "nodes": [node.dump(media_save_dir=media_save_dir) for node in self._children],
        }

    @classmethod
    def load(cls, data: dict):
        nodes = [(RefNode.load(d) if d["type"] == "ref" else CustomNode.load(d)) for d in data["nodes"]]
        return cls(data["id"], nodes)


@dataclass
class Hyper(Segment):
    """Hyper对象，表示一类超级消息。如卡片消息、ark消息、小程序等"""

    format: Literal["xml", "json"]
    raw: Optional[str] = field(default=None)
    content: Optional[Union[dict, list]] = field(default=None)

    def __post_init__(self):
        if self.raw and not self.content and self.format == "json":
            with contextlib.suppress(json.JSONDecodeError):
                self.content = json.loads(self.raw)
        if self.content and not self.raw and self.format == "json":
            with contextlib.suppress(json.JSONDecodeError):
                self.raw = json.dumps(self.content, ensure_ascii=False)


# discord: action, link -> Button
# telegram: InlineKeyboardButton & bot_command


@dataclass
class Button(Segment):
    """Button对象，表示一类按钮消息"""

    flag: Literal["action", "link", "input", "enter"]
    """
    - 点击 action 类型的按钮时会触发一个关于 按钮回调 事件，该事件的 button 资源会包含上述 id
    - 点击 link 类型的按钮时会打开一个链接或者小程序，该链接的地址为 `url`
    - 点击 input 类型的按钮时会在用户的输入框中填充 `text`
    - 点击 enter 类型的按钮时会直接发送 `text`
    """
    label: Union[str, Text]
    """按钮上的文字"""
    clicked_label: Optional[str] = None
    """点击后按钮上的文字"""
    id: Optional[str] = None
    url: Optional[str] = None
    text: Optional[str] = None
    style: Optional[str] = None
    """
    仅建议使用下列值：
    - primary
    - secondary
    - success
    - warning
    - danger
    - info
    - link
    - grey
    - blue

    此处规定 `grey` 与 `secondary` 等同, `blue` 与 `primary` 等同
    """
    permission: Union[Literal["admin", "all"], list[At]] = "all"
    """按钮权限类型
    - admin: 仅管理者可操作
    - all: 所有人可操作
    - list[At]: 指定用户/身份组可操作
    """

    def __post_init__(self):
        if self.style == "grey":
            self.style = "secondary"
        elif self.style == "blue":
            self.style = "primary"
        label = Text(self.label) if isinstance(self.label, str) else self.label[:]
        if self.flag == "link":
            label += f"({self.url})"
        elif self.flag != "action":
            label += f"[{self.text}]"
        self._children.insert(0, label)


@dataclass
class Keyboard(Segment):
    """Keyboard对象，表示一行按钮元素"""

    buttons: InitVar[Union[list[Button], None]] = field(default=None)
    id: Optional[str] = field(default=None)
    """此处一般用来表示模板id，特殊情况下可能表示例如 bot_appid 等"""
    row: Union[int, None] = None
    """当消息中只写有一个 Keyboard 时可根据此参数约定按钮组的列数"""
    _children: list[Button] = field(init=False, default_factory=list)

    def __post_init__(self, buttons: Union[list[Button], None]):
        if buttons:
            self._children.extend(buttons)

    @property
    def children(self):
        return self._children

    def __call__(self, *segments: Union[Segment, Button]) -> Self:
        if not segments:
            return self
        self._children.extend(segments)  # type: ignore
        return self


@dataclass
class Other(Segment):
    """其他 Segment"""

    origin: MessageSegment

    def __str__(self):
        return f"[{self.origin.type}]"

    def dump(self, **kwargs):
        return {
            "type": "other",
            "origin": asdict(self.origin),
            "module": self.origin.__class__.__module__,
            "class": self.origin.__class__.__name__,
        }

    @classmethod
    def load(cls, data: dict):
        module = importlib.import_module(data["module"])
        origin = getattr(module, data["class"])(**data["origin"])
        return cls(origin)


@dataclass
class I18n(Segment):
    """特殊的 Segment，用于 i18n 消息"""

    @overload
    def __init__(self, item: LangItem, /, *args, mapping: Optional[dict] = None, **kwargs): ...
    @overload
    def __init__(self, scope: str, type_: str, /, *args, mapping: Optional[dict] = None, **kwargs): ...

    def __init__(
        self,
        item_or_scope: Union[LangItem, str],
        type_: Optional[str] = None,
        /,
        *args,
        mapping: Optional[dict] = None,
        **kwargs,
    ):
        self._children = []
        if isinstance(item_or_scope, LangItem):
            self.item = item_or_scope
        elif type_:
            self.item = LangItem(item_or_scope, type_)
        else:
            raise ValueError("I18n must have lang item or scope and type")
        self.args = args
        self.kwargs = mapping or {}
        self.kwargs.update(kwargs)

    def tp(self):
        from .message import UniMessage

        return UniMessage.template(lang.require(self.item.scope, self.item.type))

    def dump(self, **kwargs):
        return {
            "type": "i18n",
            "scope": self.item.scope,
            "_type": self.item.type,
            "args": list(self.args),
            "kwargs": self.kwargs,
        }

    @classmethod
    def load(cls, data: dict):
        return cls(data["scope"], data["_type"], *data["args"], **data["kwargs"])


TM = TypeVar("TM", bound=Message)
TMS = TypeVar("TMS", bound=MessageSegment)


class _CustomMounter:
    BUILDERS: ClassVar[
        dict[
            Union[str, Callable[[MessageSegment], bool]],
            Callable[["MessageBuilder", MessageSegment], Union[Segment, None]],
        ]
    ] = {}
    EXPORTERS: ClassVar[
        dict[
            type[Segment],
            Union[
                Callable[
                    ["MessageExporter", Segment, Union[Bot, None], Union[bool, FallbackStrategy]],
                    Awaitable[Optional[MessageSegment]],
                ],
                Callable[
                    ["MessageExporter", Segment, Union[Bot, None], Union[bool, FallbackStrategy]],
                    Awaitable[list[MessageSegment]],
                ],
            ],
        ]
    ] = {}

    @classmethod
    def custom_register(cls, custom_type: type[TS], condition: Union[str, Callable[[MessageSegment], bool]]):
        def _register(func: Callable[["MessageBuilder", MessageSegment], Union[TS, None]]):
            cls.BUILDERS[condition] = func
            return func

        return _register

    def solve(self, builder: "MessageBuilder[TMS]", seg: TMS):
        for condition, func in self.BUILDERS.items():
            if isinstance(condition, str):
                if seg.type == condition:
                    return func(builder, seg)
            elif condition(seg):
                return func(builder, seg)
        return None

    @classmethod
    def custom_handler(cls, custom_type: type[TS]):
        def _handler(
            func: Union[
                Callable[
                    ["MessageExporter", TS, Union[Bot, None], Union[bool, FallbackStrategy]],
                    Awaitable[Optional[MessageSegment]],
                ],
                Callable[
                    ["MessageExporter", TS, Union[Bot, None], Union[bool, FallbackStrategy]],
                    Awaitable[list[MessageSegment]],
                ],
            ],
        ):
            cls.EXPORTERS[custom_type] = func  # type: ignore
            return func

        return _handler

    async def export(
        self,
        exporter: "MessageExporter[TM]",
        seg: Segment,
        bot: Union[Bot, None],
        fallback: Union[bool, FallbackStrategy],
    ):
        if seg.__class__ in self.EXPORTERS:
            return await self.EXPORTERS[seg.__class__](exporter, seg, bot, fallback)
        return None


custom = _CustomMounter()
custom_register = custom.custom_register
custom_handler = custom.custom_handler


env = create_local_patterns("nonebot")


env[Segment] = BasePattern(
    mode=MatchMode.KEEP,
    accepts=Union[Segment, str],
)
env[Media] = BasePattern(
    mode=MatchMode.KEEP,
    accepts=Media,
)


def apply_media_to_url(func: MediaToUrl):
    """为 Media 对象设置 to_url 方法，用于将文件或数据上传到文件服务器并返回 URL"""
    Media.to_url = func
