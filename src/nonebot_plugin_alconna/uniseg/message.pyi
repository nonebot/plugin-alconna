from collections.abc import Awaitable, Iterable, Sequence
from io import BytesIO
from pathlib import Path
from typing import Any, Callable, Literal, NoReturn, Protocol, TypeVar, overload
from typing_extensions import Self, SupportsIndex, TypeAlias

from nonebot.internal.adapter import Bot, Event, Message
from tarina.context import ContextModel
from tarina.lang.model import LangItem

from .fallback import FallbackStrategy
from .receipt import Receipt
from .segment import (
    At,
    AtAll,
    Audio,
    Button,
    CustomNode,
    Emoji,
    File,
    Hyper,
    I18n,
    Image,
    Keyboard,
    Reference,
    RefNode,
    Reply,
    Segment,
    Text,
    Video,
    Voice,
)
from .target import Target
from .template import UniMessageTemplate

_T = TypeVar("_T")
_TS = TypeVar("_TS", bound=Segment)
_TS1 = TypeVar("_TS1", bound=Segment)

_TM = TypeVar("_TM", bound=str | Message | UniMessage)

class SendWrapper(Protocol):
    async def __call__(self, bot: Bot, event: Event, send: _TM) -> _TM: ...

current_send_wrapper: ContextModel[SendWrapper] = ...

Fragment: TypeAlias = Segment | Iterable[Segment]
Visit: TypeAlias = Callable[[Segment], _T]
Render: TypeAlias = Callable[[dict[str, Any], list[Segment]], _T]
SyncTransformer: TypeAlias = bool | Fragment | Render[bool | Fragment]
AsyncTransformer: TypeAlias = bool | Fragment | Render[Awaitable[bool | Fragment]]
SyncVisitor: TypeAlias = dict[str, SyncTransformer] | Visit[bool | Fragment]
AsyncVisitor: TypeAlias = dict[str, AsyncTransformer] | Visit[Awaitable[bool | Fragment]]

MessageContainer: TypeAlias = str | Segment | Sequence[MessageContainer] | UniMessage

class UniMessage(list[_TS]):
    @classmethod
    @overload
    def text(cls_or_self: UniMessage | type[UniMessage], text: str) -> UniMessage[Text]: ...
    @classmethod
    @overload
    def text(cls_or_self: UniMessage[_TS1] | type[UniMessage[_TS1]], text: str) -> UniMessage[_TS1 | Text]: ...
    @classmethod
    @overload
    def style(cls_or_self: UniMessage | type[UniMessage], content: str, *style: str) -> UniMessage[Text]: ...
    @classmethod
    @overload
    def style(
        cls_or_self: UniMessage[_TS1] | type[UniMessage[_TS1]], content: str, *style: str
    ) -> UniMessage[_TS1 | Text]: ...
    @classmethod
    @overload
    def at(cls_or_self: UniMessage | type[UniMessage], user_id: str) -> UniMessage[At]: ...
    @classmethod
    @overload
    def at(cls_or_self: UniMessage[_TS1] | type[UniMessage[_TS1]], user_id: str) -> UniMessage[_TS1 | At]: ...
    @classmethod
    @overload
    def at_role(cls_or_self: UniMessage | type[UniMessage], role_id: str) -> UniMessage[At]: ...
    @classmethod
    @overload
    def at_role(cls_or_self: UniMessage[_TS1] | type[UniMessage[_TS1]], role_id: str) -> UniMessage[_TS1 | At]: ...
    @classmethod
    @overload
    def at_channel(cls_or_self: UniMessage | type[UniMessage], channel_id: str) -> UniMessage[At]: ...
    @classmethod
    @overload
    def at_channel(
        cls_or_self: UniMessage[_TS1] | type[UniMessage[_TS1]], channel_id: str
    ) -> UniMessage[_TS1 | At]: ...
    @classmethod
    @overload
    def at_all(cls_or_self: UniMessage | type[UniMessage], online: bool = False) -> UniMessage[AtAll]: ...
    @classmethod
    @overload
    def at_all(
        cls_or_self: UniMessage[_TS1] | type[UniMessage[_TS1]], online: bool = False
    ) -> UniMessage[_TS1 | AtAll]: ...
    @classmethod
    @overload
    def emoji(cls_or_self: UniMessage | type[UniMessage], id: str, name: str | None = None) -> UniMessage[Emoji]: ...
    @classmethod
    @overload
    def emoji(
        cls_or_self: UniMessage[_TS1] | type[UniMessage[_TS1]], id: str, name: str | None = None
    ) -> UniMessage[_TS1 | Emoji]: ...
    @classmethod
    @overload
    def image(
        cls_or_self: UniMessage | type[UniMessage],
        id: str | None = None,
        url: str | None = None,
        path: str | Path | None = None,
        raw: bytes | BytesIO | None = None,
        mimetype: str | None = None,
        width: int | None = None,
        height: int | None = None,
        sticker: bool = False,
        name: str = "image.png",
    ) -> UniMessage[Image]: ...
    @classmethod
    @overload
    def image(
        cls_or_self: UniMessage[_TS1] | type[UniMessage[_TS1]],
        id: str | None = None,
        url: str | None = None,
        path: str | Path | None = None,
        raw: bytes | BytesIO | None = None,
        mimetype: str | None = None,
        width: int | None = None,
        height: int | None = None,
        sticker: bool = False,
        name: str = "image.png",
    ) -> UniMessage[_TS1 | Image]: ...
    @classmethod
    @overload
    def video(
        cls_or_self: UniMessage | type[UniMessage],
        id: str | None = None,
        url: str | None = None,
        path: str | Path | None = None,
        raw: bytes | BytesIO | None = None,
        mimetype: str | None = None,
        thumbnail: Image | None = None,
        name: str = "video.mp4",
    ) -> UniMessage[Video]: ...
    @classmethod
    @overload
    def video(
        cls_or_self: UniMessage[_TS1] | type[UniMessage[_TS1]],
        id: str | None = None,
        url: str | None = None,
        path: str | Path | None = None,
        raw: bytes | BytesIO | None = None,
        mimetype: str | None = None,
        thumbnail: Image | None = None,
        name: str = "video.mp4",
    ) -> UniMessage[_TS1 | Video]: ...
    @classmethod
    @overload
    def voice(
        cls_or_self: UniMessage | type[UniMessage],
        id: str | None = None,
        url: str | None = None,
        path: str | Path | None = None,
        raw: bytes | BytesIO | None = None,
        mimetype: str | None = None,
        duration: float | None = None,
        name: str = "voice.wav",
    ) -> UniMessage[Voice]: ...
    @classmethod
    @overload
    def voice(
        cls_or_self: UniMessage[_TS1] | type[UniMessage[_TS1]],
        id: str | None = None,
        url: str | None = None,
        path: str | Path | None = None,
        raw: bytes | BytesIO | None = None,
        mimetype: str | None = None,
        duration: float | None = None,
        name: str = "voice.wav",
    ) -> UniMessage[_TS1 | Voice]: ...
    @classmethod
    @overload
    def audio(
        cls_or_self: UniMessage | type[UniMessage],
        id: str | None = None,
        url: str | None = None,
        path: str | Path | None = None,
        raw: bytes | BytesIO | None = None,
        mimetype: str | None = None,
        duration: float | None = None,
        name: str = "audio.mp3",
    ) -> UniMessage[Audio]: ...
    @classmethod
    @overload
    def audio(
        cls_or_self: UniMessage[_TS1] | type[UniMessage[_TS1]],
        id: str | None = None,
        url: str | None = None,
        path: str | Path | None = None,
        raw: bytes | BytesIO | None = None,
        mimetype: str | None = None,
        duration: float | None = None,
        name: str = "audio.mp3",
    ) -> UniMessage[_TS1 | Audio]: ...
    @classmethod
    @overload
    def file(
        cls_or_self: UniMessage | type[UniMessage],
        id: str | None = None,
        url: str | None = None,
        path: str | Path | None = None,
        raw: bytes | BytesIO | None = None,
        mimetype: str | None = None,
        name: str = "file.bin",
    ) -> UniMessage[File]: ...
    @classmethod
    @overload
    def file(
        cls_or_self: UniMessage[_TS1] | type[UniMessage[_TS1]],
        id: str | None = None,
        url: str | None = None,
        path: str | Path | None = None,
        raw: bytes | BytesIO | None = None,
        mimetype: str | None = None,
        name: str = "file.bin",
    ) -> UniMessage[_TS1 | File]: ...
    @classmethod
    @overload
    def reply(cls_or_self: UniMessage | type[UniMessage], id: str) -> UniMessage[Reply]: ...
    @classmethod
    @overload
    def reply(cls_or_self: UniMessage[_TS1] | type[UniMessage[_TS1]], id: str) -> UniMessage[_TS1 | Reply]: ...
    @classmethod
    @overload
    def hyper(
        cls_or_self: UniMessage | type[UniMessage],
        flag: Literal["xml", "json"],
        content: str,
    ) -> UniMessage[Hyper]: ...
    @classmethod
    @overload
    def hyper(
        cls_or_self: UniMessage[_TS1] | type[UniMessage[_TS1]],
        flag: Literal["xml", "json"],
        content: str,
    ) -> UniMessage[_TS1 | Hyper]: ...
    @classmethod
    @overload
    def reference(
        cls_or_self: UniMessage | type[UniMessage],
        *nodes: RefNode | CustomNode,
        id: str | None = None,
    ) -> UniMessage[Reference]: ...
    @classmethod
    @overload
    def reference(
        cls_or_self: UniMessage[_TS1] | type[UniMessage[_TS1]],
        *nodes: RefNode | CustomNode,
        id: str | None = None,
    ) -> UniMessage[_TS1 | Reference]: ...
    @classmethod
    @overload
    def keyboard(
        cls_or_self: UniMessage | type[UniMessage],
        *buttons: Button,
        id: str | None = None,
        row: int | None = None,
    ) -> UniMessage[Keyboard]: ...
    @classmethod
    @overload
    def keyboard(
        cls_or_self: UniMessage[_TS1] | type[UniMessage[_TS1]],
        *buttons: Button,
        id: str | None = None,
        row: int | None = None,
    ) -> UniMessage[_TS1 | Keyboard]: ...
    @classmethod
    @overload
    def i18n(
        cls_or_self: UniMessage | type[UniMessage],
        item_or_scope: LangItem | str,
        type_: str | None = None,
        /,
        *args,
        mapping: dict | None = None,
        **kwargs,
    ) -> UniMessage[I18n]: ...
    @classmethod
    @overload
    def i18n(
        cls_or_self: UniMessage[_TS1] | type[UniMessage[_TS1]],
        item_or_scope: LangItem | str,
        type_: str | None = None,
        /,
        *args,
        mapping: dict | None = None,
        **kwargs,
    ) -> UniMessage[_TS1 | I18n]: ...
    @overload
    def __init__(self): ...
    @overload
    def __init__(self: UniMessage[Text], message: str): ...
    @overload
    def __init__(self, message: _TS): ...
    @overload
    def __init__(self: UniMessage[_TS1], message: _TS1): ...
    @overload
    def __init__(self, message: Iterable[_TS]): ...
    @overload
    def __init__(self: UniMessage[_TS1], message: Iterable[_TS1]): ...
    @overload
    def __init__(self: UniMessage[Text], message: Iterable[str]): ...
    @overload
    def __init__(self: UniMessage[Text | _TS1], message: Iterable[str | _TS1]): ...
    @classmethod
    def template(cls, format_string: str | UniMessage) -> UniMessageTemplate: ...
    def __merge_text__(self) -> Self: ...
    @overload
    def __add__(self, other: str) -> UniMessage[_TS | Text]: ...
    @overload
    def __add__(self, other: _TS | Iterable[_TS]) -> UniMessage[_TS]: ...
    @overload
    def __add__(self, other: _TS1 | Iterable[_TS1]) -> UniMessage[_TS | _TS1]: ...
    @overload
    def __radd__(self, other: str) -> UniMessage[Text | _TS]: ...
    @overload
    def __radd__(self, other: _TS | Iterable[_TS]) -> UniMessage[_TS]: ...
    @overload
    def __radd__(self, other: _TS1 | Iterable[_TS1]) -> UniMessage[_TS1 | _TS]: ...
    def __iadd__(self, other: str | _TS | Iterable[_TS], _merge: bool = True) -> Self: ...
    @overload
    def __getitem__(self, args: type[_TS1]) -> UniMessage[_TS1]: ...
    @overload
    def __getitem__(self, args: tuple[type[_TS1], int]) -> _TS1: ...
    @overload
    def __getitem__(self, args: tuple[type[_TS1], slice]) -> UniMessage[_TS1]: ...
    @overload
    def __getitem__(self, args: int) -> _TS: ...
    @overload
    def __getitem__(self, args: slice) -> UniMessage[_TS]: ...
    def __contains__(self, value: str | Segment | type[Segment]) -> bool: ...
    def has(self, value: str | Segment | type[Segment]) -> bool: ...
    def index(self, value: str | Segment | type[Segment], *args: SupportsIndex) -> int: ...
    def get(self, type_: type[_TS], count: int | None = None) -> UniMessage[_TS]: ...
    def count(self, value: type[Segment] | str | Segment) -> int: ...
    def only(self, value: type[Segment] | str | Segment) -> bool: ...
    def join(self, iterable: Iterable[_TS1 | UniMessage[_TS1]]) -> UniMessage[_TS | _TS1]: ...
    def copy(self) -> UniMessage[_TS]: ...
    def include(self, *types: type[Segment]) -> UniMessage[_TS]: ...
    def exclude(self, *types: type[Segment]) -> UniMessage[_TS]: ...
    def extract_plain_text(self) -> str: ...
    def filter(self, predicate: Callable[[_TS], bool]) -> UniMessage[_TS]: ...
    @overload
    def map(self, func: Callable[[_TS], _TS1]) -> UniMessage[_TS1]: ...
    @overload
    def map(self, func: Callable[[_TS], _T]) -> list[_T]: ...
    def select(self, cls: type[_TS1]) -> UniMessage[_TS1]: ...
    def transform(self, rules: SyncVisitor) -> UniMessage: ...
    async def transform_async(self, rules: AsyncVisitor) -> UniMessage: ...
    def split(self, pattern: str = " ") -> list[Self]: ...
    def replace(
        self,
        old: str,
        new: str | Text,
    ) -> Self: ...
    def startswith(self, string: str) -> bool: ...
    def endswith(self, string: str) -> bool: ...
    def removeprefix(self, prefix: str) -> Self: ...
    def removesuffix(self, suffix: str) -> Self: ...
    def strip(self, *segments: str | Segment | type[Segment]) -> Self: ...
    def lstrip(self, *segments: str | Segment | type[Segment]) -> Self: ...
    def rstrip(self, *segments: str | Segment | type[Segment]) -> Self: ...
    @classmethod
    def of(cls, message: Message, bot: Bot | None = None, adapter: str | None = None) -> UniMessage: ...
    async def attach_reply(self, event: Event | None = None, bot: Bot | None = None) -> Self: ...
    async def export(
        self,
        bot: Bot | None = None,
        fallback: bool | FallbackStrategy = ...,
        adapter: str | None = None,
    ) -> Message: ...
    def export_sync(
        self,
        fallback: bool | FallbackStrategy = ...,
        adapter: str | None = None,
    ) -> Message: ...
    async def send(
        self,
        target: Event | Target | None = None,
        bot: Bot | None = None,
        fallback: bool | FallbackStrategy = ...,
        at_sender: str | bool = False,
        reply_to: str | bool | Reply | None = False,
        no_wrapper: bool = False,
        **kwargs,
    ) -> Receipt: ...
    async def finish(
        self,
        target: Event | Target | None = None,
        bot: Bot | None = None,
        fallback: bool | FallbackStrategy = ...,
        at_sender: str | bool = False,
        reply_to: str | bool | Reply | None = False,
        **kwargs,
    ) -> NoReturn: ...
    @overload
    def dump(self, media_save_dir: str | Path | bool | None = None) -> list[dict]: ...
    @overload
    def dump(self, media_save_dir: str | Path | bool | None = None, json: Literal[True] = True) -> str: ...
    @classmethod
    def load(cls: type[UniMessage[Segment]], data: str | list[dict[str, Any]]): ...
