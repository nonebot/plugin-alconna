"""通用标注, 无法用于创建 MS对象"""

import re
import json
import contextlib
from io import BytesIO
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
from typing_extensions import Self
from collections.abc import Iterable, Awaitable
from dataclasses import InitVar, field, asdict, dataclass
from typing import TYPE_CHECKING, Any, Union, Literal, TypeVar, Callable, ClassVar, Optional, Protocol, overload

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
        return asdict(self)

    def __call__(self, *segments: Union[str, "Segment"]) -> Self:
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


STYLE_TYPE_MAP = {
    "bold": "\033[1m",
    "italic": "\033[3m",
    "underline": "\033[4m",
    "strikethrough": "\033[9m",
    "obfuscated": "\033[47m",
    "code": "\033[7m",
    "spoiler": "\033[8m",
    "link": "\033[96m",
    "reset": "\033[0m",
    "black": "\033[30m",
    "dark_blue": "\033[34m",
    "dark_green": "\033[32m",
    "dark_aqua": "\033[36m",
    "dark_red": "\033[31m",
    "dark_purple": "\033[35m",
    "gold": "\033[33m",
    "gray": "\033[37m",
    "dark_gray": "\033[90m",
    "blue": "\033[94m",
    "green": "\033[92m",
    "aqua": "\033[96m",
    "red": "\033[91m",
    "light_purple": "\033[95m",
    "yellow": "\033[93m",
    "white": "\033[97m",
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
            prefix = "".join(f"{STYLE_TYPE_MAP[style]}" for style in styles[scale])
            result.append(f"{prefix}{text[scale[0] : scale[1]]}\033[0m")
        right = scales[-1][1]
        result.append(text[right:])
        text = "".join(result)
        return text

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
        res = Text(
            self.text[item],
            {
                (max(_start - start, 0), _end - start): style
                for (_start, _end), style in self.styles.items()
                if _start < end and _end > start
            },
        )
        res.__merge__()
        return res

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


@dataclass
class Image(Media):
    """Image对象, 表示一类图片元素"""

    name: str = field(default="image.png")

    __default_name__ = "image.png"


@dataclass
class Audio(Media):
    """Audio对象, 表示一类音频元素"""

    duration: Optional[int] = field(default=None)
    name: str = field(default="audio.mp3")

    __default_name__ = "audio.mp3"


@dataclass
class Voice(Media):
    """Voice对象, 表示一类语音元素"""

    duration: Optional[int] = field(default=None)
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


@dataclass
class RefNode:
    """表示转发消息的引用消息元素"""

    id: str
    """消息id"""
    context: Optional[str] = None
    """可能的群聊id"""


@dataclass
class CustomNode:
    """表示转发消息的自定义消息元素"""

    uid: str
    """消息发送者id"""
    name: str
    """消息发送者昵称"""
    content: Union[str, "UniMessage", Message]
    """消息内容"""
    time: datetime = field(default_factory=datetime.now)
    """消息发送时间"""
    context: Optional[str] = None
    """可能的群聊id"""


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
        self._children.insert(0, Text(self.label) if isinstance(self.label, str) else self.label)


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


TM = TypeVar("TM", bound=Message)
TMS = TypeVar("TMS", bound=MessageSegment)


class _CustomMounter:
    BUILDERS: dict[
        Union[str, Callable[[MessageSegment], bool]], Callable[["MessageBuilder", MessageSegment], Union[Segment, None]]
    ] = {}
    EXPORTERS: dict[
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
            ]
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


def apply_media_to_url(func: MediaToUrl):
    """为 Media 对象设置 to_url 方法，用于将文件或数据上传到文件服务器并返回 URL"""
    Media.to_url = func
