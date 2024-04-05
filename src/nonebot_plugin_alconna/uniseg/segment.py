"""通用标注, 无法用于创建 MS对象"""

import re
import abc
import json
import contextlib
from io import BytesIO
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
from dataclasses import field, asdict
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Type,
    Tuple,
    Union,
    Literal,
    TypeVar,
    Callable,
    ClassVar,
    Iterable,
    Optional,
    Protocol,
    Awaitable,
    overload,
)

from nonebot.compat import PYDANTIC_V2, ConfigDict
from nonebot.internal.adapter import Bot, Message, MessageSegment
from nepattern import MatchMode, BasePattern, create_local_patterns

from .utils import fleep

if TYPE_CHECKING:
    from .message import UniMessage

if TYPE_CHECKING:
    from dataclasses import dataclass
else:
    from pydantic.dataclasses import dataclass as _dataclass

    if PYDANTIC_V2:
        config = ConfigDict(arbitrary_types_allowed=True)
    else:

        class config:
            arbitrary_types_allowed = True

    def dataclass(*args, **kwargs):
        return _dataclass(*args, config=config, **kwargs)


TS = TypeVar("TS", bound="Segment")
TS1 = TypeVar("TS1", bound="Segment")


class Segment:
    """基类标注"""

    if TYPE_CHECKING:
        origin: MessageSegment  # = field(init=False, repr=False, compare=False)

    def __str__(self):
        return f"[{self.__class__.__name__.lower()}]"

    def __repr__(self):
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.data.items())
        return f"{self.__class__.__name__}({attrs})"

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
    def data(self) -> Dict[str, Any]:
        try:
            return asdict(self)  # type: ignore
        except TypeError:
            return vars(self)


STYLE_TYPE_MAP = {
    "bold": "\033[1m",
    "italic": "\033[3m",
    "underline": "\033[4m",
    "strikethrough": "\033[9m",
    "obfuscated": "\033[47m",
    "code": "\033[7m",
    "spoiler": "\033[8m",
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
    styles: Dict[Tuple[int, int], List[str]] = field(default_factory=dict)

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
        data1 = {}
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

    def mark(self, start: int, end: int, *styles: str):
        _styles = self.styles.setdefault((start, end), [])
        for sty in styles:
            if sty not in _styles:
                _styles.append(sty)
        self.__merge__()
        return self

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

    def extract_most_styles(self) -> List[str]:
        if not self.styles:
            return []
        max_scale = max(self.styles, key=lambda x: x[1] - x[0], default=(0, 0))
        return self.styles[max_scale]


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
        self, data: Union[str, Path, bytes, BytesIO], bot: Bot, name: Optional[str] = None
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

    def __post_init__(self):
        if self.path:
            self.name = Path(self.path).name
        if self.url and not urlparse(self.url).hostname:
            self.url = f"https://{self.url}"

    @property
    def raw_bytes(self) -> bytes:
        if not self.raw:
            raise ValueError(f"{self} has no raw data")
        raw = self.raw.getvalue() if isinstance(self.raw, BytesIO) else self.raw
        header = raw[:128]
        info = fleep.get(header)
        self.mimetype = info.mimes[0] if info.mimes else self.mimetype
        if info.types and info.extensions:
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

    name: str = field(default="video.mp4")

    __default_name__ = "video.mp4"


@dataclass
class File(Media):
    """File对象, 表示一类文件元素"""

    name: str = field(default="file.bin")

    __default_name__ = "file.bin"


@dataclass
class Reply(Segment):
    """Reply对象，表示一类回复消息"""

    id: str
    """此处不一定是消息ID，可能是其他ID，如消息序号等"""
    msg: Optional[Union[Message, str]] = field(default=None)
    origin: Optional[Any] = field(default=None)


@dataclass
class RefNode:
    """表示转发消息的引用消息元素"""

    id: str
    context: Optional[str] = None


@dataclass
class CustomNode:
    """表示转发消息的自定义消息元素"""

    uid: str
    name: str
    time: datetime
    content: Union[str, List[Segment], Message]


@dataclass
class Reference(Segment):
    """Reference对象，表示一类引用消息。转发消息 (Forward) 也属于此类"""

    id: Optional[str] = field(default=None)
    """此处不一定是消息ID，可能是其他ID，如消息序号等"""
    content: Optional[Union[Message, str, List[Union[RefNode, CustomNode]]]] = field(default=None)


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


@dataclass
class Other(Segment):
    """其他 Segment"""

    origin: MessageSegment

    def __str__(self):
        return f"[{self.origin.type}]"


TM = TypeVar("TM", bound=Message)


@dataclass
class Custom(Segment, abc.ABC):
    """Custom对象，表示一类自定义消息"""

    mstype: str
    content: Any

    @abc.abstractmethod
    def export(self, msg_type: Type[TM]) -> MessageSegment[TM]: ...

    @property
    def type(self) -> str:
        return self.mstype


TCustom = TypeVar("TCustom", bound=Custom)


class _CustomBuilder:
    BUILDERS: Dict[Union[str, Callable[[MessageSegment], bool]], Callable[[MessageSegment], Union[Custom, None]]] = {}

    @classmethod
    def custom_register(cls, custom_type: Type[TCustom], condition: Union[str, Callable[[MessageSegment], bool]]):
        def _register(func: Callable[[MessageSegment], Union[TCustom, None]]):
            cls.BUILDERS[condition] = func
            return func

        return _register

    def solve(self, seg: MessageSegment):
        for condition, func in self.BUILDERS.items():
            if isinstance(condition, str):
                if seg.type == condition:
                    return func(seg)
            elif condition(seg):
                return func(seg)


custom = _CustomBuilder()
custom_register = custom.custom_register


env = create_local_patterns("nonebot")


env[Segment] = BasePattern(
    mode=MatchMode.KEEP,
    origin=Segment,
    accepts=Segment,
)


def apply_media_to_url(func: MediaToUrl):
    """为 Media 对象设置 to_url 方法，用于将文件或数据上传到文件服务器并返回 URL"""
    Media.to_url = func
