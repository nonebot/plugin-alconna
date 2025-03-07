from __future__ import annotations

import asyncio
from io import BytesIO
from pathlib import Path
from copy import deepcopy
from json import dumps, loads
from types import FunctionType
from dataclasses import dataclass
from collections.abc import Iterable, Sequence, Awaitable
from typing_extensions import Self, TypeAlias, SupportsIndex
from typing import TYPE_CHECKING, Any, Union, Literal, TypeVar, Callable, NoReturn, Protocol, overload

from tarina import lang
from tarina.lang.model import LangItem
from tarina.context import ContextModel
from nonebot.compat import custom_validation
from nonebot.exception import FinishedException
from nonebot.internal.adapter import Bot, Event, Message
from nonebot.internal.matcher import current_bot, current_event

from .target import Target
from .exporter import MessageExporter
from .constraint import SerializeFailed
from .template import UniMessageTemplate
from .fallback import FallbackMessage, FallbackStrategy
from .adapters import alter_get_builder, alter_get_exporter
from .segment import (
    At,
    File,
    I18n,
    Text,
    AtAll,
    Audio,
    Emoji,
    Hyper,
    Image,
    Reply,
    Video,
    Voice,
    Button,
    RefNode,
    Segment,
    Keyboard,
    Reference,
    CustomNode,
    get_segment_class,
)

T = TypeVar("T")
TS = TypeVar("TS", bound=Segment)
TS1 = TypeVar("TS1", bound=Segment)


class _method:
    def __init__(self, func: FunctionType):
        self.__func__ = func

    def __get__(self, instance, owner):
        if instance is None:
            return self.__func__.__get__(owner, owner)
        return self.__func__.__get__(instance, owner)


TM = TypeVar("TM", bound=Union[str, Message, "UniMessage"])


class SendWrapper(Protocol):
    async def __call__(self, bot: Bot, event: Event, send: TM) -> TM: ...


current_send_wrapper: ContextModel[SendWrapper] = ContextModel("nonebot_plugin_alconna.uniseg.send_wrapper")


Fragment: TypeAlias = Union[Segment, Iterable[Segment]]
Visit: TypeAlias = Callable[[Segment], T]
Render: TypeAlias = Callable[[dict[str, Any], list[Segment]], T]
SyncTransformer: TypeAlias = Union[bool, Fragment, Render[Union[bool, Fragment]]]
AsyncTransformer: TypeAlias = Union[bool, Fragment, Render[Awaitable[Union[bool, Fragment]]]]
SyncVisitor: TypeAlias = Union[dict[str, SyncTransformer], Visit[Union[bool, Fragment]]]
AsyncVisitor: TypeAlias = Union[dict[str, AsyncTransformer], Visit[Awaitable[Union[bool, Fragment]]]]

MessageContainer = Union[str, Segment, Sequence["MessageContainer"], "UniMessage"]


class UniMessage(list[TS]):
    """通用消息序列

    参数:
        message: 消息内容
    """

    if TYPE_CHECKING:

        @classmethod
        def text(
            cls_or_self: UniMessage[TS1] | type[UniMessage[TS1]], text: str  # type: ignore
        ) -> UniMessage[TS1 | Text]:
            """创建纯文本消息

            参数:
                text: 文本内容

            返回:
                构建的消息
            """
            ...

        @classmethod
        def style(
            cls_or_self: UniMessage[TS1] | type[UniMessage[TS1]], content: str, *style: str  # type: ignore
        ) -> UniMessage[TS1 | Text]:
            """创建带样式的文本消息

            参数:
                content: 文本内容
                style: 样式

            返回:
                构建的消息
            """
            ...

        @classmethod
        def at(
            cls_or_self: UniMessage[TS1] | type[UniMessage[TS1]], user_id: str  # type: ignore
        ) -> UniMessage[TS1 | At]:
            """创建 @用户 消息

            参数:
                user_id: 要 @ 的用户 ID

            返回:
                构建的消息
            """
            ...

        @classmethod
        def at_role(
            cls_or_self: UniMessage[TS1] | type[UniMessage[TS1]], role_id: str  # type: ignore
        ) -> UniMessage[TS1 | At]:
            """创建 @角色组 消息

            参数:
                role_id: 要 @ 的角色 ID

            返回:
                构建的消息
            """
            ...

        @classmethod
        def at_channel(
            cls_or_self: UniMessage[TS1] | type[UniMessage[TS1]], channel_id: str  # type: ignore
        ) -> UniMessage[TS1 | At]:
            """创建 #频道 消息

            参数:
                channel_id: 要 @ 的频道 ID

            返回:
                构建的消息
            """
            ...

        @classmethod
        def at_all(
            cls_or_self: UniMessage[TS1] | type[UniMessage[TS1]],  # type: ignore
            online: bool = False,
        ) -> UniMessage[TS1 | AtAll]:
            """创建 @全体成员 消息

            参数:
                online: 是否只 @ 在线成员

            返回:
                构建的消息
            """
            ...

        @classmethod
        def emoji(
            cls_or_self: UniMessage[TS1] | type[UniMessage[TS1]],  # type: ignore
            id: str,
            name: str | None = None,
        ) -> UniMessage[TS1 | Emoji]:
            """创建 emoji 消息

            参数:
                id: emoji ID
                name: emoji 名称

            返回:
                构建的消息
            """
            ...

        @classmethod
        def image(
            cls_or_self: UniMessage[TS1] | type[UniMessage[TS1]],  # type: ignore
            id: str | None = None,
            url: str | None = None,
            path: str | Path | None = None,
            raw: bytes | BytesIO | None = None,
            mimetype: str | None = None,
            width: int | None = None,
            height: int | None = None,
            name: str = "image.png",
        ) -> UniMessage[TS1 | Image]:
            """创建图片消息

            参数:
                id: 图片 ID
                url: 图片链接
                path: 图片路径
                raw: 图片原始数据
                mimetype: 图片 MIME 类型
                name: 图片名称
                width: 图片宽度
                height: 图片高度
            返回:
                构建的消息
            """
            ...

        @classmethod
        def video(
            cls_or_self: UniMessage[TS1] | type[UniMessage[TS1]],  # type: ignore
            id: str | None = None,
            url: str | None = None,
            path: str | Path | None = None,
            raw: bytes | BytesIO | None = None,
            mimetype: str | None = None,
            thumbnail: Image | None = None,
            name: str = "video.mp4",
        ) -> UniMessage[TS1 | Video]:
            """创建视频消息

            参数:
                id: 视频 ID
                url: 视频链接
                path: 视频路径
                raw: 视频原始数据
                mimetype: 视频 MIME 类型
                thumbnail: 视频缩略图
                name: 视频名称
            返回:
                构建的消息
            """
            ...

        @classmethod
        def voice(
            cls_or_self: UniMessage[TS1] | type[UniMessage[TS1]],  # type: ignore
            id: str | None = None,
            url: str | None = None,
            path: str | Path | None = None,
            raw: bytes | BytesIO | None = None,
            mimetype: str | None = None,
            duration: float | None = None,
            name: str = "voice.wav",
        ) -> UniMessage[TS1 | Voice]:
            """创建语音消息

            参数:
                id: 语音 ID
                url: 语音链接
                path: 语音路径
                raw: 语音原始数据
                mimetype: 语音 MIME 类型
                duration: 语音时长
                name: 语音名称
            返回:
                构建的消息
            """
            ...

        @classmethod
        def audio(
            cls_or_self: UniMessage[TS1] | type[UniMessage[TS1]],  # type: ignore
            id: str | None = None,
            url: str | None = None,
            path: str | Path | None = None,
            raw: bytes | BytesIO | None = None,
            mimetype: str | None = None,
            duration: float | None = None,
            name: str = "audio.mp3",
        ) -> UniMessage[TS1 | Audio]:
            """创建音频消息

            参数:
                id: 音频 ID
                url: 音频链接
                path: 音频路径
                raw: 音频原始数据
                mimetype: 音频 MIME 类型
                duration: 音频时长
                name: 音频名称
            返回:
                构建的消息
            """
            ...

        @classmethod
        def file(
            cls_or_self: UniMessage[TS1] | type[UniMessage[TS1]],  # type: ignore
            id: str | None = None,
            url: str | None = None,
            path: str | Path | None = None,
            raw: bytes | BytesIO | None = None,
            mimetype: str | None = None,
            name: str = "file.bin",
        ) -> UniMessage[TS1 | File]:
            """创建文件消息

            参数:
                id: 文件 ID
                url: 文件链接
                path: 文件路径
                raw: 文件原始数据
                mimetype: 文件 MIME 类型
                name: 文件名称
            返回:
                构建的消息
            """
            ...

        @classmethod
        def reply(
            cls_or_self: UniMessage[TS1] | type[UniMessage[TS1]], id: str  # type: ignore
        ) -> UniMessage[TS1 | Reply]:
            """创建回复消息

            参数:
                id: 回复消息 ID

            返回:
                构建的消息
            """
            ...

        @classmethod
        def hyper(
            cls_or_self: UniMessage[TS1] | type[UniMessage[TS1]],  # type: ignore
            flag: Literal["xml", "json"],
            content: str,
        ) -> UniMessage[TS1 | Hyper]:
            """创建卡片消息

            参数:
                flag: 卡片类型
                content: 卡片内容

            返回:
                构建的消息
            """
            ...

        @classmethod
        def reference(
            cls_or_self: UniMessage[TS1] | type[UniMessage[TS1]],  # type: ignore
            *nodes: RefNode | CustomNode,
            id: str | None = None,
        ) -> UniMessage[TS1 | Reference]:
            """创建转发消息

            参数:
                nodes: 转发消息节点
                id: 此处不一定是消息ID，可能是其他ID，如消息序号等

            返回:
                构建的消息
            """
            ...

        @classmethod
        def keyboard(
            cls_or_self: UniMessage[TS1] | type[UniMessage[TS1]],  # type: ignore
            *buttons: Button,
            id: str | None = None,
            row: int | None = None,
        ) -> UniMessage[TS1 | Keyboard]:
            """创建转发消息

            参数:
                buttons: 按钮
                id: 此处一般用来表示模板id，特殊情况下可能表示例如 bot_appid 等
                row: 当消息中只写有一个 Keyboard 时可根据此参数约定按钮组的列数

            返回:
                构建的消息
            """
            ...

        @classmethod
        def i18n(
            cls_or_self: UniMessage[TS1] | type[UniMessage[TS1]],  # type: ignore
            item_or_scope: LangItem | str,
            type_: str | None = None,
            /,
            *args,
            mapping: dict | None = None,
            **kwargs,
        ) -> UniMessage[TS1 | I18n]:
            """创建 i18n 消息"""
            ...

    else:

        @_method
        def text(cls_or_self, text: str) -> UniMessage[TS1 | Text]:
            if isinstance(cls_or_self, UniMessage):
                cls_or_self.append(Text(text))
                return cls_or_self
            return UniMessage(Text(text))

        @_method
        def style(cls_or_self, content: str, *style: str) -> UniMessage[TS1 | Text]:
            if isinstance(cls_or_self, UniMessage):
                cls_or_self.append(Text(content).mark(None, None, *style))
                return cls_or_self
            return UniMessage(Text(content).mark(None, None, *style))

        @_method
        def at(cls_or_self, user_id: str) -> UniMessage[TS1 | At]:
            if isinstance(cls_or_self, UniMessage):
                cls_or_self.append(At("user", user_id))
                return cls_or_self
            return UniMessage(At("user", user_id))

        @_method
        def at_role(cls_or_self, role_id: str) -> UniMessage[TS1 | At]:
            if isinstance(cls_or_self, UniMessage):
                cls_or_self.append(At("role", role_id))
                return cls_or_self
            return UniMessage(At("role", role_id))

        @_method
        def at_channel(cls_or_self, channel_id: str) -> UniMessage[TS1 | At]:
            if isinstance(cls_or_self, UniMessage):
                cls_or_self.append(At("channel", channel_id))
                return cls_or_self
            return UniMessage(At("channel", channel_id))

        @_method
        def at_all(cls_or_self, online: bool = False) -> UniMessage[TS1 | AtAll]:
            if isinstance(cls_or_self, UniMessage):
                cls_or_self.append(AtAll(online))
                return cls_or_self
            return UniMessage(AtAll(online))

        @_method
        def emoji(cls_or_self, id: str, name: str | None = None) -> UniMessage[TS1 | Emoji]:
            if isinstance(cls_or_self, UniMessage):
                cls_or_self.append(Emoji(id, name))
                return cls_or_self
            return UniMessage(Emoji(id, name))

        @_method
        def image(
            cls_or_self,
            id: str | None = None,
            url: str | None = None,
            path: str | Path | None = None,
            raw: bytes | BytesIO | None = None,
            mimetype: str | None = None,
            width: int | None = None,
            height: int | None = None,
            name: str = "image.png",
        ) -> UniMessage[TS1 | Image]:
            if isinstance(cls_or_self, UniMessage):
                cls_or_self.append(Image(id, url, path, raw, mimetype, name, width, height))
                return cls_or_self
            return UniMessage(Image(id, url, path, raw, mimetype, name, width, height))

        @_method
        def video(
            cls_or_self,
            id: str | None = None,
            url: str | None = None,
            path: str | Path | None = None,
            raw: bytes | BytesIO | None = None,
            mimetype: str | None = None,
            thumbnail: Image | None = None,
            name: str = "video.mp4",
        ) -> UniMessage[TS1 | Video]:
            if isinstance(cls_or_self, UniMessage):
                cls_or_self.append(Video(id, url, path, raw, mimetype, name, thumbnail))
                return cls_or_self
            return UniMessage(Video(id, url, path, raw, mimetype, name, thumbnail))

        @_method
        def voice(
            cls_or_self,
            id: str | None = None,
            url: str | None = None,
            path: str | Path | None = None,
            raw: bytes | BytesIO | None = None,
            mimetype: str | None = None,
            duration: float | None = None,
            name: str = "voice.wav",
        ) -> UniMessage[TS1 | Voice]:
            if isinstance(cls_or_self, UniMessage):
                cls_or_self.append(Voice(id, url, path, raw, mimetype, name, duration))
                return cls_or_self
            return UniMessage(Voice(id, url, path, raw, mimetype, name, duration))

        @_method
        def audio(
            cls_or_self,
            id: str | None = None,
            url: str | None = None,
            path: str | Path | None = None,
            raw: bytes | BytesIO | None = None,
            mimetype: str | None = None,
            duration: float | None = None,
            name: str = "audio.mp3",
        ) -> UniMessage[TS1 | Audio]:
            if isinstance(cls_or_self, UniMessage):
                cls_or_self.append(Audio(id, url, path, raw, mimetype, name, duration))
                return cls_or_self
            return UniMessage(Audio(id, url, path, raw, mimetype, name, duration))

        @_method
        def file(
            cls_or_self,
            id: str | None = None,
            url: str | None = None,
            path: str | Path | None = None,
            raw: bytes | BytesIO | None = None,
            mimetype: str | None = None,
            name: str = "file.bin",
        ) -> UniMessage[TS1 | File]:
            if isinstance(cls_or_self, UniMessage):
                cls_or_self.append(File(id, url, path, raw, mimetype, name))
                return cls_or_self
            return UniMessage(File(id, url, path, raw, mimetype, name))

        @_method
        def reply(cls_or_self, id: str) -> UniMessage[TS1 | Reply]:
            if isinstance(cls_or_self, UniMessage):
                cls_or_self.append(Reply(id))
                return cls_or_self
            return UniMessage(Reply(id))

        @_method
        def hyper(cls_or_self, flag: Literal["xml", "json"], content: str) -> UniMessage[TS1 | Hyper]:
            if isinstance(cls_or_self, UniMessage):
                cls_or_self.append(Hyper(flag, content))
                return cls_or_self
            return UniMessage(Hyper(flag, content))

        @_method
        def reference(cls_or_self, *nodes: RefNode | CustomNode, id: str | None = None) -> UniMessage[TS1 | Reference]:
            if isinstance(cls_or_self, UniMessage):
                cls_or_self.append(Reference(id=id, nodes=list(nodes)))
                return cls_or_self
            return UniMessage(Reference(id=id, nodes=list(nodes)))

        @_method
        def keyboard(
            cls_or_self,
            *buttons: Button,
            id: str | None = None,
            row: int | None = None,
        ) -> UniMessage[TS1 | Keyboard]:
            if isinstance(cls_or_self, UniMessage):
                cls_or_self.append(Keyboard(id=id, buttons=list(buttons), row=row))
                return cls_or_self
            return UniMessage(Keyboard(id=id, buttons=list(buttons), row=row))

        @_method
        def i18n(
            cls_or_self,
            item_or_scope: LangItem | str,
            type_: str | None = None,
            /,
            *args,
            mapping: dict | None = None,
            **kwargs,
        ) -> UniMessage[TS1 | I18n]:
            if isinstance(cls_or_self, UniMessage):
                cls_or_self.append(I18n(item_or_scope, type_, *args, mapping=mapping, **kwargs))  # type: ignore
                return cls_or_self
            return UniMessage(I18n(item_or_scope, type_, *args, mapping=mapping, **kwargs))  # type: ignore

    @overload
    def __init__(self): ...

    @overload
    def __init__(self: UniMessage[Text], message: str): ...

    @overload
    def __init__(self, message: TS): ...

    @overload
    def __init__(self: UniMessage[TS1], message: TS1): ...

    @overload
    def __init__(self, message: Iterable[TS]): ...

    @overload
    def __init__(self: UniMessage[TS1], message: Iterable[TS1]): ...

    @overload
    def __init__(self: UniMessage[Text], message: Iterable[str]): ...

    @overload
    def __init__(self: UniMessage[Text | TS1], message: Iterable[str | TS1]): ...

    def __init__(
        self: UniMessage[Segment],
        message: Iterable[str | TS] | str | TS | None = None,
    ):
        super().__init__()
        if isinstance(message, str):
            self.__iadd__(Text(message), _merge=False)
        elif isinstance(message, Iterable):
            for i in message:
                self.__iadd__(Text(i) if isinstance(i, str) else i)
        elif isinstance(message, Segment):
            self.__iadd__(message, _merge=False)
        self.__merge_text__()

    def __str__(self) -> str:
        return "".join(str(seg) for seg in self)

    def __repr__(self) -> str:
        return "[" + ", ".join(repr(seg) for seg in self) + "]"

    @classmethod
    def template(cls, format_string: str | UniMessage) -> UniMessageTemplate:
        """创建消息模板。

        用法和 `str.format` 大致相同，支持以 `UniMessage` 对象作为消息模板并输出消息对象。
        并且提供了拓展的格式化控制符，可以通过 `Segment` 的实例化方法创建消息。

        参数:
            format_string: 格式化模板

        返回:
            消息格式化器
        """
        return UniMessageTemplate(format_string, cls)  # type: ignore

    def __merge_text__(self) -> Self:
        if not self:
            return self
        result = []
        last = list.__getitem__(self, 0)
        for seg in list.__getitem__(self, slice(1, None)):
            if isinstance(seg, Text) and isinstance(last, Text):
                last += seg
            else:
                result.append(last)
                last = seg
        result.append(last)
        self.clear()
        self.extend(result)
        return self

    @overload
    def __add__(self, other: str) -> UniMessage[TS | Text]: ...

    @overload
    def __add__(self, other: TS | Iterable[TS]) -> UniMessage[TS]: ...

    @overload
    def __add__(self, other: TS1 | Iterable[TS1]) -> UniMessage[TS | TS1]: ...

    def __add__(self, other: str | TS | TS1 | Iterable[TS | TS1]) -> UniMessage:
        result: UniMessage = self.copy()
        if isinstance(other, str):
            if result and isinstance(text := result[-1], Text):
                text.text += other
            else:
                result.append(Text(other))
        elif isinstance(other, Segment):
            result.append(other)
        elif isinstance(other, Iterable):
            for seg in other:
                result += seg
        else:
            raise TypeError(f"Unsupported type {type(other)!r}")
        result.__merge_text__()
        return result

    @overload
    def __radd__(self, other: str) -> UniMessage[Text | TS]: ...

    @overload
    def __radd__(self, other: TS | Iterable[TS]) -> UniMessage[TS]: ...

    @overload
    def __radd__(self, other: TS1 | Iterable[TS1]) -> UniMessage[TS1 | TS]: ...

    def __radd__(self, other: str | TS1 | Iterable[TS1]) -> UniMessage:
        result = UniMessage(other)
        return result + self

    def __iadd__(self, other: str | TS | Iterable[TS], _merge: bool = True) -> Self:
        if isinstance(other, str):
            if self and isinstance(text := self[-1], Text):
                text.text += other
            else:
                self.append(Text(other))  # type: ignore
        elif isinstance(other, Segment):
            self.append(other)
        elif isinstance(other, Iterable):
            for seg in other:
                self.__iadd__(seg, _merge)
        else:
            raise TypeError(f"Unsupported type {type(other)!r}")
        if _merge:
            self.__merge_text__()
        return self

    @overload
    def __getitem__(self, args: type[TS1]) -> UniMessage[TS1]:
        """获取仅包含指定消息段类型的消息

        参数:
            args: 消息段类型

        返回:
            所有类型为 `args` 的消息段
        """

    @overload
    def __getitem__(self, args: tuple[type[TS1], int]) -> TS1:
        """索引指定类型的消息段

        参数:
            args: 消息段类型和索引

        返回:
            类型为 `args[0]` 的消息段第 `args[1]` 个
        """

    @overload
    def __getitem__(self, args: tuple[type[TS1], slice]) -> UniMessage[TS1]:
        """切片指定类型的消息段

        参数:
            args: 消息段类型和切片

        返回:
            类型为 `args[0]` 的消息段切片 `args[1]`
        """

    @overload
    def __getitem__(self, args: int) -> TS:
        """索引消息段

        参数:
            args: 索引

        返回:
            第 `args` 个消息段
        """

    @overload
    def __getitem__(self, args: slice) -> UniMessage[TS]:
        """切片消息段

        参数:
            args: 切片

        返回:
            消息切片 `args`
        """

    def __getitem__(
        self,
        args: type[TS1] | tuple[type[TS1], int] | tuple[type[TS1], slice] | int | slice,
    ) -> TS | TS1 | UniMessage[TS] | UniMessage[TS1]:
        arg1, arg2 = args if isinstance(args, tuple) else (args, None)
        if isinstance(arg1, int) and arg2 is None:
            return list.__getitem__(self, arg1)
        if isinstance(arg1, slice) and arg2 is None:
            return UniMessage(list.__getitem__(self, arg1))
        if TYPE_CHECKING:
            assert not isinstance(arg1, (slice, int))
        if issubclass(arg1, Segment) and arg2 is None:
            return UniMessage(seg for seg in self if isinstance(seg, arg1))
        if issubclass(arg1, Segment) and isinstance(arg2, int):
            return [seg for seg in self if isinstance(seg, arg1)][arg2]
        if issubclass(arg1, Segment) and isinstance(arg2, slice):
            return UniMessage([seg for seg in self if isinstance(seg, arg1)][arg2])
        raise ValueError("Incorrect arguments to slice")  # pragma: no cover

    def __contains__(self, value: str | Segment | type[Segment]) -> bool:
        """检查消息段是否存在

        参数:
            value: 消息段或消息段类型
        返回:
            消息内是否存在给定消息段或给定类型的消息段
        """
        if isinstance(value, type):
            return bool(next((seg for seg in self if isinstance(seg, value)), None))
        if isinstance(value, str):
            value = Text(value)
        return super().__contains__(value)

    def has(self, value: str | Segment | type[Segment]) -> bool:
        """与 {ref}``__contains__` <nonebot.adapters.Message.__contains__>` 相同"""
        return value in self

    def index(self, value: str | Segment | type[Segment], *args: SupportsIndex) -> int:
        """索引消息段

        参数:
            value: 消息段或者消息段类型
            arg: start 与 end

        返回:
            索引 index

        异常:
            ValueError: 消息段不存在
        """
        if isinstance(value, type):
            first_segment = next((seg for seg in self if isinstance(seg, value)), None)
            if first_segment is None:
                raise ValueError(f"Segment with type {value!r} is not in message")
            return super().index(first_segment, *args)
        if isinstance(value, str):
            value = Text(value)
        return super().index(value, *args)  # type: ignore

    def get(self, type_: type[TS], count: int | None = None) -> UniMessage[TS]:
        """获取指定类型的消息段

        参数:
            type_: 消息段类型
            count: 获取个数

        返回:
            构建的新消息
        """
        if count is None:
            return self[type_]

        iterator, filtered = (seg for seg in self if isinstance(seg, type_)), UniMessage()
        for _ in range(count):
            seg = next(iterator, None)
            if seg is None:
                break
            filtered.append(seg)
        return filtered  # type: ignore

    def count(self, value: type[Segment] | str | Segment) -> int:
        """计算指定消息段的个数

        参数:
            value: 消息段或消息段类型

        返回:
            个数
        """
        if isinstance(value, str):
            value = Text(value)
        return (
            len(self[value])  # type: ignore
            if isinstance(value, type)
            else super().count(value)  # type: ignore
        )

    def only(self, value: type[Segment] | str | Segment) -> bool:
        """检查消息中是否仅包含指定消息段

        参数:
            value: 指定消息段或消息段类型

        返回:
            是否仅包含指定消息段
        """
        if isinstance(value, type):
            return all(isinstance(seg, value) for seg in self)
        if isinstance(value, str):
            value = Text(value)
        return all(seg == value for seg in self)

    def join(self, iterable: Iterable[TS1 | UniMessage[TS1]]) -> UniMessage[TS | TS1]:
        """将多个消息连接并将自身作为分割

        参数:
            iterable: 要连接的消息

        返回:
            连接后的消息
        """
        ret = UniMessage()
        for index, msg in enumerate(iterable):
            if index != 0:
                ret.extend(self)
            if isinstance(msg, Segment):
                ret.append(msg)
            else:
                ret.extend(msg.copy())
        return ret  # type: ignore

    def copy(self) -> UniMessage[TS]:
        """深拷贝消息"""
        return deepcopy(self)

    def include(self, *types: type[Segment]) -> UniMessage[TS]:
        """过滤消息

        参数:
            types: 包含的消息段类型

        返回:
            新构造的消息
        """
        return UniMessage(seg for seg in self if seg.__class__ in types)

    def exclude(self, *types: type[Segment]) -> UniMessage[TS]:
        """过滤消息

        参数:
            types: 不包含的消息段类型

        返回:
            新构造的消息
        """
        return UniMessage(seg for seg in self if seg.__class__ not in types)

    def extract_plain_text(self) -> str:
        """提取消息内纯文本消息"""

        return "".join(seg.text for seg in self if isinstance(seg, Text))

    def filter(self, predicate: Callable[[TS], bool]) -> UniMessage[TS]:
        """过滤消息

        参数:
            target: 消息段类型
            predicate: 过滤函数
        """
        return UniMessage(seg for seg in self if predicate(seg))

    @overload
    def map(self, func: Callable[[TS], TS1]) -> UniMessage[TS1]: ...

    @overload
    def map(self, func: Callable[[TS], T]) -> list[T]: ...

    def map(self, func: Callable[[TS], TS1] | Callable[[TS], T]) -> UniMessage[TS1] | list[T]:
        result1 = []
        result2 = []
        for seg in self:
            result = func(seg)
            if isinstance(result, Segment):
                result1.append(result)
            else:
                result2.append(result)
        if result1:
            return UniMessage(result1)
        return result2

    def select(self, cls: type[TS1]) -> UniMessage[TS1]:
        """递归地从消息中选择指定类型的消息段"""

        def query(segs: list[Segment]):
            for s in segs:
                if isinstance(s, cls):
                    yield s
                yield from query(s.children)

        results = []
        for seg in self:
            if isinstance(seg, cls):
                results.append(seg)
            results.extend(query(seg.children))
        return UniMessage(results)

    @staticmethod
    def _visit_sync(seg: Segment, rules: SyncVisitor):
        _type, data, children = seg.type, seg.data, seg.children
        if not isinstance(rules, dict):
            return rules(seg)
        result = rules.get(_type, True)
        if not isinstance(result, (bool, Segment, Iterable)):
            result = result(data, children)
        return result

    @staticmethod
    async def _visit_async(seg: Segment, rules: AsyncVisitor):
        _type, data, children = seg.type, seg.data, seg.children
        if not isinstance(rules, dict):
            return await rules(seg)
        result = rules.get(_type, True)
        if not isinstance(result, (bool, Segment, Iterable)):
            result = await result(data, children)
        return result

    def transform(self, rules: SyncVisitor) -> UniMessage:
        """同步遍历消息段并转换

        参数:
            rules: 转换规则

        返回:
            转换后的消息
        """
        output = UniMessage()
        for seg in self:
            result = self._visit_sync(seg, rules)
            if result is True:
                output.append(seg)
            elif result is not False:
                if isinstance(result, Segment):
                    output.append(result)
                else:
                    output.extend(result)
        output.__merge_text__()
        return output

    async def transform_async(self, rules: AsyncVisitor) -> UniMessage:
        """异步遍历消息段并转换

        参数:
            rules: 转换规则

        返回:
            转换后的消息
        """
        output = UniMessage()
        for seg in self:
            result = await self._visit_async(seg, rules)
            if result is True:
                output.append(seg)
            elif result is not False:
                if isinstance(result, Segment):
                    output.append(result)
                else:
                    output.extend(result)
        output.__merge_text__()
        return output

    def split(self, pattern: str = " ") -> list[Self]:
        """和 `str.split` 差不多, 提供一个字符串, 然后返回分割结果.

        Args:
            pattern (str): 分隔符. 默认为单个空格.

        Returns:
            list[Self]: 分割结果, 行为和 `str.split` 差不多.
        """

        result: list[Self] = []
        tmp = []
        for seg in self:
            if isinstance(seg, Text):
                split_result = seg.split(pattern)
                for index, split_text in enumerate(split_result):
                    if tmp and index > 0:
                        result.append(self.__class__(tmp))
                        tmp = []
                    if split_text.text:
                        tmp.append(split_text)
            else:
                tmp.append(seg)
        if tmp:
            result.append(self.__class__(tmp))
            tmp = []
        return result

    def replace(
        self,
        old: str,
        new: str | Text,
    ) -> Self:
        """替换消息中有关的文本

        Args:
            old (str): 要替换的字符串.
            new (str | Text): 替换后的字符串/文本元素.

        Returns:
            UniMessage: 修改后的消息链, 若未替换则原样返回.
        """
        result_list: list[TS] = []
        for seg in self:
            if isinstance(seg, Text):
                result_list.append(seg.replace(old, new))  # type: ignore
            else:
                result_list.append(seg)
        return self.__class__(result_list)

    def startswith(self, string: str) -> bool:
        """判断消息链是否以给出的字符串开头

        Args:
            string (str): 字符串

        Returns:
            bool: 是否以给出的字符串开头
        """

        if not self or not isinstance(self[0], Text):
            return False
        return list.__getitem__(self, 0).text.startswith(string)

    def endswith(self, string: str) -> bool:
        """判断消息链是否以给出的字符串结尾

        Args:
            string (str): 字符串

        Returns:
            bool: 是否以给出的字符串结尾
        """

        if not self or not isinstance(self[-1], Text):
            return False
        return list.__getitem__(self, -1).text.endswith(string)

    def removeprefix(self, prefix: str) -> Self:
        """移除消息链前缀.

        Args:
            prefix (str): 要移除的前缀.

        Returns:
            UniMessage: 修改后的消息链.
        """
        copy = list.copy(self)
        if not copy:
            return self.__class__(copy)
        seg = copy[0]
        if not isinstance(seg, Text):
            return self.__class__(copy)
        if seg.text.startswith(prefix):
            seg = seg[len(prefix) :]
            if not seg.text:
                copy.pop(0)
            else:
                copy[0] = seg
        return self.__class__(copy)

    def removesuffix(self, suffix: str) -> Self:
        """移除消息链后缀.

        Args:
            suffix (str): 要移除的后缀.

        Returns:
            UniMessage: 修改后的消息链.
        """
        copy = list.copy(self)
        if not copy:
            return self.__class__(copy)
        seg = copy[-1]
        if not isinstance(seg, Text):
            return self.__class__(copy)
        if seg.text.endswith(suffix):
            seg = seg[: -len(suffix)]
            if not seg.text:
                copy.pop(-1)
            else:
                copy[-1] = seg
        return self.__class__(copy)

    def strip(self, *segments: str | Segment | type[Segment]) -> Self:
        return self.lstrip(*segments).rstrip(*segments)

    def lstrip(self, *segments: str | Segment | type[Segment]) -> Self:
        types = [i for i in segments if not isinstance(i, str)] or []
        chars = "".join([i for i in segments if isinstance(i, str)]) or None
        copy = list.copy(self)
        if not copy:
            return self.__class__(copy)
        while copy:
            seg = copy[0]
            if seg in types or seg.__class__ in types:
                copy.pop(0)
            elif isinstance(seg, Text):
                seg = seg.lstrip(chars)
                if not seg.text:
                    copy.pop(0)
                    continue
                copy[0] = seg
                break
            else:
                break
        return self.__class__(copy)

    def rstrip(self, *segments: str | Segment | type[Segment]) -> Self:
        types = [i for i in segments if not isinstance(i, str)] or []
        chars = "".join([i for i in segments if isinstance(i, str)]) or None
        copy = list.copy(self)
        if not copy:
            return self.__class__(copy)
        while copy:
            seg = copy[-1]
            if seg in types or seg.__class__ in types:
                copy.pop(-1)
            elif isinstance(seg, Text):
                seg = seg.rstrip(chars)
                if not seg.text:
                    copy.pop(-1)
                    continue
                copy[-1] = seg
                break
            else:
                break
        return self.__class__(copy)

    @staticmethod
    async def generate(
        *,
        message: Message | None = None,
        event: Event | None = None,
        bot: Bot | None = None,
        adapter: str | None = None,
    ) -> UniMessage:
        if not message:
            if not event:
                try:
                    event = current_event.get()
                except LookupError as e:
                    raise SerializeFailed(lang.require("nbp-uniseg", "event_missing")) from e
            try:
                message = event.get_message()
            except Exception:
                return UniMessage()
        if not adapter:
            if not bot:
                try:
                    bot = current_bot.get()
                except LookupError as e:
                    raise SerializeFailed(lang.require("nbp-uniseg", "bot_missing")) from e
            _adapter = bot.adapter
            adapter = _adapter.get_name()
        if not (fn := alter_get_builder(adapter)):
            raise SerializeFailed(lang.require("nbp-uniseg", "unsupported").format(adapter=adapter))
        result = UniMessage(fn.generate(message))
        if (event and bot) and (_reply := await fn.extract_reply(event, bot)):
            if result.has(Reply) and result.index(Reply) == 0:
                result.pop(0)
            result.insert(0, _reply)
        return result

    @staticmethod
    def generate_sync(
        *,
        message: Message | None = None,
        event: Event | None = None,
        bot: Bot | None = None,
        adapter: str | None = None,
    ) -> UniMessage:
        if not message:
            if not event:
                try:
                    event = current_event.get()
                except LookupError as e:
                    raise SerializeFailed(lang.require("nbp-uniseg", "event_missing")) from e
            try:
                message = event.get_message()
            except Exception:
                return UniMessage()
        if not adapter:
            if not bot:
                try:
                    bot = current_bot.get()
                except LookupError as e:
                    raise SerializeFailed(lang.require("nbp-uniseg", "bot_missing")) from e
            _adapter = bot.adapter
            adapter = _adapter.get_name()
        if not (fn := alter_get_builder(adapter)):
            raise SerializeFailed(lang.require("nbp-uniseg", "unsupported").format(adapter=adapter))
        return UniMessage(fn.generate(message))

    generate_without_reply = generate_sync

    @staticmethod
    def get_message_id(event: Event | None = None, bot: Bot | None = None, adapter: str | None = None) -> str:
        if not event:
            try:
                event = current_event.get()
            except LookupError as e:
                raise SerializeFailed(lang.require("nbp-uniseg", "event_missing")) from e
        if hasattr(event, "__uniseg_message_id__"):
            return event.__uniseg_message_id__  # type: ignore
        if not adapter:
            if not bot:
                try:
                    bot = current_bot.get()
                except LookupError as e:
                    raise SerializeFailed(lang.require("nbp-uniseg", "bot_missing")) from e
            _adapter = bot.adapter
            adapter = _adapter.get_name()
        if fn := alter_get_exporter(adapter):
            setattr(event, "__uniseg_message_id__", msg_id := fn.get_message_id(event))
            return msg_id
        raise SerializeFailed(lang.require("nbp-uniseg", "unsupported").format(adapter=adapter))

    @staticmethod
    def get_target(event: Event | None = None, bot: Bot | None = None, adapter: str | None = None) -> Target:
        if not event:
            try:
                event = current_event.get()
            except LookupError as e:
                raise SerializeFailed(lang.require("nbp-uniseg", "event_missing")) from e
        if not adapter:
            if not bot:
                try:
                    bot = current_bot.get()
                except LookupError as e:
                    raise SerializeFailed(lang.require("nbp-uniseg", "bot_missing")) from e
            _adapter = bot.adapter
            adapter = _adapter.get_name()
        if fn := alter_get_exporter(adapter):
            return fn.get_target(event, bot)
        raise SerializeFailed(lang.require("nbp-uniseg", "unsupported").format(adapter=adapter))

    def _handle_i18n(self, extra: dict, *args, **kwargs):
        segments = [*self]
        self.clear()
        for seg in segments:
            if not isinstance(seg, I18n):
                self.append(seg)
            else:
                msg = seg.tp().format(*args, *seg.args, **kwargs, **seg.kwargs, **extra)
                if msg.has(I18n):
                    msg._handle_i18n(extra, *seg.args, **seg.kwargs)
                self.extend(msg)  # type: ignore
        self.__merge_text__()

    async def export(
        self,
        bot: Bot | None = None,
        fallback: bool | FallbackStrategy = FallbackStrategy.rollback,
        adapter: str | None = None,
    ) -> Message:
        """将 UniMessage 转换为指定适配器下的 Message"""
        if not adapter:
            if not bot:
                try:
                    bot = current_bot.get()
                except LookupError as e:
                    raise SerializeFailed(lang.require("nbp-uniseg", "bot_missing")) from e
            adapter = bot.adapter.get_name()
        if self.has(I18n):
            extra = {}
            try:
                event = current_event.get()
                extra["$event"] = event
                extra["$target"] = self.get_target(event, bot, adapter)
                msg_id = UniMessage.get_message_id(event, bot, adapter)
                extra["$message_id"] = msg_id
            except (LookupError, NotImplementedError, SerializeFailed):
                pass
            self._handle_i18n(extra)
        try:
            if fn := alter_get_exporter(adapter):
                return await fn.export(self, bot, fallback)
            raise SerializeFailed(lang.require("nbp-uniseg", "unsupported").format(adapter=adapter))
        except SerializeFailed:
            if fallback and fallback != FallbackStrategy.forbid:
                return FallbackMessage(str(self))
            raise

    def export_sync(
        self,
        fallback: bool | FallbackStrategy = FallbackStrategy.rollback,
        adapter: str | None = None,
    ) -> Message:
        """（实验性）同步方法地将 UniMessage 转换为指定适配器下的 Message"""
        coro = self.export(None, fallback, adapter)
        try:
            return coro.send(None)
        except StopIteration as e:
            return e.args[0]

    async def send(
        self,
        target: Event | Target | None = None,
        bot: Bot | None = None,
        fallback: bool | FallbackStrategy = FallbackStrategy.rollback,
        at_sender: str | bool = False,
        reply_to: str | bool | Reply | None = False,
        no_wrapper: bool = False,
        **kwargs,
    ) -> Receipt:
        if not target:
            try:
                target = current_event.get()
            except LookupError as e:
                raise SerializeFailed(lang.require("nbp-uniseg", "event_missing")) from e
        if not bot:
            try:
                bot = current_bot.get()
            except LookupError as e:
                if not isinstance(target, Target):
                    raise SerializeFailed(lang.require("nbp-uniseg", "bot_missing")) from e
                try:
                    bot = await target.select()
                except Exception as e1:
                    raise SerializeFailed(lang.require("nbp-uniseg", "bot_missing")) from e1
        if at_sender:
            if isinstance(at_sender, str):
                self.insert(0, At("user", at_sender))  # type: ignore
            elif isinstance(target, Event):
                self.insert(0, At("user", target.get_user_id()))  # type: ignore
            else:
                raise TypeError("at_sender must be str when target is not Event")
        if reply_to:
            if isinstance(reply_to, Reply):
                self.insert(0, reply_to)  # type: ignore
            else:
                if isinstance(reply_to, bool):
                    if isinstance(target, Event):
                        reply_to = self.get_message_id(target, bot)
                    else:
                        raise TypeError("reply_to must be str when target is not Event")
                self.insert(0, Reply(reply_to))  # type: ignore
        if not no_wrapper and isinstance(target, Event) and (wrapper := current_send_wrapper.get(None)):
            self[:] = await wrapper(bot, target, self)
        msg = await self.export(bot, fallback)
        adapter = bot.adapter
        adapter_name = adapter.get_name()
        if not (fn := alter_get_exporter(adapter_name)):
            raise SerializeFailed(lang.require("nbp-uniseg", "unsupported").format(adapter=adapter_name))
        res = await fn.send_to(target, bot, msg, **kwargs)
        return Receipt(bot, target, fn, res if isinstance(res, list) else [res])

    async def finish(
        self,
        target: Event | Target | None = None,
        bot: Bot | None = None,
        fallback: bool | FallbackStrategy = FallbackStrategy.rollback,
        at_sender: str | bool = False,
        reply_to: str | bool | Reply | None = False,
        **kwargs,
    ) -> NoReturn:
        await self.send(target, bot, fallback, at_sender, reply_to, **kwargs)
        raise FinishedException

    @overload
    def dump(self, media_save_dir: str | Path | bool | None = None) -> list[dict]: ...

    @overload
    def dump(self, media_save_dir: str | Path | bool | None = None, json: Literal[True] = True) -> str: ...

    def dump(self, media_save_dir: str | Path | bool | None = None, json: bool = False) -> str | list[dict[str, Any]]:
        """将消息序列化为 JSON 格式

        注意：
            若 media_save_dir 为 False，则不会保存媒体文件。
            若 media_save_dir 为 True，则会将文件数据转为 base64 编码。
            若不指定 media_save_dir，则会尝试导入 `nonebot_plugin_localstore` 并使用其提供的路径。
            否则，将会尝试使用当前工作目录。

        Args:
            media_save_dir (Union[str, Path， bool, None], optional): 媒体文件保存路径. Defaults to None.
            json (bool, optional): 是否返回 JSON 字符串. Defaults to False.

        Returns:
            Union[str, list[dict]]: 序列化后的消息
        """
        result = [seg.dump(media_save_dir=media_save_dir) for seg in self]
        return dumps(result, ensure_ascii=False) if json else result

    @classmethod
    def load(cls: type[UniMessage[Segment]], data: str | list[dict[str, Any]]):
        """从 JSON 数据加载消息

        Args:
            data (Union[str, list[dict[str, Any]]]): JSON 数据

        Returns:
            UniMessage: 加载后的消息
        """
        if isinstance(data, str):
            _data: list[dict[str, Any]] = loads(data)
        else:
            _data = data
        return cls(get_segment_class(seg_data["type"]).load(seg_data) for seg_data in _data)


@custom_validation
@dataclass
class Receipt:
    bot: Bot
    context: Event | Target
    exporter: MessageExporter
    msg_ids: list[Any]

    @property
    def recallable(self) -> bool:
        return self.exporter.__class__.recall != MessageExporter.recall

    @property
    def editable(self) -> bool:
        return self.exporter.__class__.edit != MessageExporter.edit

    def get_reply(self, index: int = -1) -> Reply | None:
        if not self.msg_ids:
            return None
        try:
            msg_id = self.msg_ids[index]
        except IndexError:
            msg_id = self.msg_ids[0]
        if not msg_id:
            return None
        try:
            return self.exporter.get_reply(msg_id)
        except NotImplementedError:
            return None

    async def recall(self, delay: float = 0, index: int = -1):
        if not self.msg_ids:
            return self
        if delay > 1e-4:
            await asyncio.sleep(delay)
        try:
            msg_id = self.msg_ids[index]
        except IndexError:
            msg_id = self.msg_ids[0]
        if not msg_id:
            return self
        try:
            await self.exporter.recall(msg_id, self.bot, self.context)
        except NotImplementedError:
            pass
        else:
            self.msg_ids.remove(msg_id)
        return self

    async def edit(
        self,
        message: str | Iterable[str] | Iterable[Segment] | Iterable[str | Segment] | Segment,
        delay: float = 0,
        index: int = -1,
    ):
        if not self.msg_ids:
            return self
        if delay > 1e-4:
            await asyncio.sleep(delay)
        message = UniMessage(message)
        msg = await self.exporter.export(message, self.bot, True)
        try:
            msg_id = self.msg_ids[index]
        except IndexError:
            msg_id = self.msg_ids[0]
        if not msg_id:
            return self
        try:
            res = await self.exporter.edit(msg, msg_id, self.bot, self.context)
        except NotImplementedError:
            return self
        else:
            if res:
                if isinstance(res, list):
                    self.msg_ids.remove(msg_id)
                    self.msg_ids.extend(res)
                else:
                    self.msg_ids[index] = res
            return self

    async def send(
        self,
        message: str | Iterable[str] | Iterable[Segment] | Iterable[str | Segment] | Segment,
        fallback: bool | FallbackStrategy = FallbackStrategy.rollback,
        at_sender: str | bool = False,
        reply_to: str | bool | Reply | None = False,
        delay: float = 0,
        **kwargs,
    ):
        if delay > 1e-4:
            await asyncio.sleep(delay)
        message = UniMessage(message)
        if at_sender:
            if isinstance(at_sender, str):
                message.insert(0, At("user", at_sender))  # type: ignore
            elif isinstance(self.context, Event):
                message.insert(0, At("user", self.context.get_user_id()))  # type: ignore
            else:
                raise TypeError("at_sender must be str when target is not Event")
        if reply_to:
            if isinstance(reply_to, Reply):
                message.insert(0, reply_to)  # type: ignore
            else:
                if isinstance(reply_to, bool):
                    if isinstance(self.context, Event):
                        reply_to = self.exporter.get_message_id(self.context)
                    else:
                        raise TypeError("reply_to must be str when target is not Event")
                self.insert(0, Reply(reply_to))  # type: ignore
        if (wrapper := current_send_wrapper.get(None)) and isinstance(self.context, Event):
            message = await wrapper(self.bot, self.context, message)
        msg = await self.exporter.export(message, self.bot, fallback)
        res = await self.exporter.send_to(self.context, self.bot, msg, **kwargs)
        self.msg_ids.extend(res if isinstance(res, list) else [res])
        return self

    async def reply(
        self,
        message: str | Iterable[str] | Iterable[Segment] | Iterable[str | Segment] | Segment,
        fallback: bool | FallbackStrategy = FallbackStrategy.rollback,
        at_sender: str | bool = False,
        index: int = -1,
        delay: float = 0,
        **kwargs,
    ):
        return await self.send(message, fallback, at_sender, self.get_reply(index), delay, **kwargs)

    async def finish(
        self,
        message: str | Iterable[str] | Iterable[Segment] | Iterable[str | Segment] | Segment,
        fallback: bool | FallbackStrategy = FallbackStrategy.rollback,
        at_sender: str | bool = False,
        reply_to: str | bool | Reply | None = False,
        delay: float = 0,
        **kwargs,
    ):
        await self.send(message, fallback, at_sender, reply_to, delay, **kwargs)
        raise FinishedException

    @classmethod
    def __get_validators__(cls):
        yield cls._validate

    @classmethod
    def _validate(cls, value) -> Self:
        if isinstance(value, cls):
            return value
        raise ValueError(f"Type {type(value)} can not be converted to {cls}")
