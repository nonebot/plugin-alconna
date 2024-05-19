import asyncio
from io import BytesIO
from pathlib import Path
from copy import deepcopy
from types import FunctionType
from dataclasses import dataclass
from collections.abc import Iterable
from typing_extensions import Self, SupportsIndex
from typing import TYPE_CHECKING, Any, Union, Literal, TypeVar, NoReturn, Optional, overload

from tarina import lang
from tarina.lang.model import LangItem
from nonebot.exception import FinishedException
from nonebot.internal.adapter import Bot, Event, Message
from nonebot.internal.matcher import current_bot, current_event

from .target import Target
from .exporter import MessageExporter
from .fallback import FallbackMessage
from .constraint import SerializeFailed
from .template import UniMessageTemplate
from .adapters import BUILDER_MAPPING, EXPORTER_MAPPING
from .segment import At, File, I18n, Text, AtAll, Audio, Emoji, Hyper, Image, Reply, Video, Voice, Segment

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


class UniMessage(list[TS]):
    """通用消息序列

    参数:
        message: 消息内容
    """

    if TYPE_CHECKING:

        @classmethod
        def text(
            cls_or_self: Union["UniMessage[TS1]", type["UniMessage[TS1]"]], text: str  # type: ignore
        ) -> "UniMessage[Union[TS1, Text]]":
            """创建纯文本消息

            参数:
                text: 文本内容

            返回:
                构建的消息
            """
            ...

        @classmethod
        def at(
            cls_or_self: Union["UniMessage[TS1]", type["UniMessage[TS1]"]], user_id: str  # type: ignore
        ) -> "UniMessage[Union[TS1, At]]":
            """创建 @用户 消息

            参数:
                user_id: 要 @ 的用户 ID

            返回:
                构建的消息
            """
            ...

        @classmethod
        def at_role(
            cls_or_self: Union["UniMessage[TS1]", type["UniMessage[TS1]"]], role_id: str  # type: ignore
        ) -> "UniMessage[Union[TS1, At]]":
            """创建 @角色组 消息

            参数:
                role_id: 要 @ 的角色 ID

            返回:
                构建的消息
            """
            ...

        @classmethod
        def at_channel(
            cls_or_self: Union["UniMessage[TS1]", type["UniMessage[TS1]"]], channel_id: str  # type: ignore
        ) -> "UniMessage[Union[TS1, At]]":
            """创建 #频道 消息

            参数:
                channel_id: 要 @ 的频道 ID

            返回:
                构建的消息
            """
            ...

        @classmethod
        def at_all(
            cls_or_self: Union["UniMessage[TS1]", type["UniMessage[TS1]"]],  # type: ignore
            online: bool = False,
        ) -> "UniMessage[Union[TS1, AtAll]]":
            """创建 @全体成员 消息

            参数:
                online: 是否只 @ 在线成员

            返回:
                构建的消息
            """
            ...

        @classmethod
        def emoji(
            cls_or_self: Union["UniMessage[TS1]", type["UniMessage[TS1]"]],  # type: ignore
            id: str,
            name: Optional[str] = None,
        ) -> "UniMessage[Union[TS1, Emoji]]":
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
            cls_or_self: Union["UniMessage[TS1]", type["UniMessage[TS1]"]],  # type: ignore
            id: Optional[str] = None,
            url: Optional[str] = None,
            path: Optional[Union[str, Path]] = None,
            raw: Optional[Union[bytes, BytesIO]] = None,
            mimetype: Optional[str] = None,
            name: str = "image.png",
        ) -> "UniMessage[Union[TS1, Image]]":
            """创建图片消息

            参数:
                id: 图片 ID
                url: 图片链接
                path: 图片路径
                raw: 图片原始数据
                mimetype: 图片 MIME 类型
                name: 图片名称
            返回:
                构建的消息
            """
            ...

        @classmethod
        def video(
            cls_or_self: Union["UniMessage[TS1]", type["UniMessage[TS1]"]],  # type: ignore
            id: Optional[str] = None,
            url: Optional[str] = None,
            path: Optional[Union[str, Path]] = None,
            raw: Optional[Union[bytes, BytesIO]] = None,
            mimetype: Optional[str] = None,
            name: str = "video.mp4",
        ) -> "UniMessage[Union[TS1, Video]]":
            """创建视频消息

            参数:
                id: 视频 ID
                url: 视频链接
                path: 视频路径
                raw: 视频原始数据
                mimetype: 视频 MIME 类型
                name: 视频名称
            返回:
                构建的消息
            """
            ...

        @classmethod
        def voice(
            cls_or_self: Union["UniMessage[TS1]", type["UniMessage[TS1]"]],  # type: ignore
            id: Optional[str] = None,
            url: Optional[str] = None,
            path: Optional[Union[str, Path]] = None,
            raw: Optional[Union[bytes, BytesIO]] = None,
            mimetype: Optional[str] = None,
            name: str = "voice.wav",
        ) -> "UniMessage[Union[TS1, Voice]]":
            """创建语音消息

            参数:
                id: 语音 ID
                url: 语音链接
                path: 语音路径
                raw: 语音原始数据
                mimetype: 语音 MIME 类型
                name: 语音名称
            返回:
                构建的消息
            """
            ...

        @classmethod
        def audio(
            cls_or_self: Union["UniMessage[TS1]", type["UniMessage[TS1]"]],  # type: ignore
            id: Optional[str] = None,
            url: Optional[str] = None,
            path: Optional[Union[str, Path]] = None,
            raw: Optional[Union[bytes, BytesIO]] = None,
            mimetype: Optional[str] = None,
            name: str = "audio.mp3",
        ) -> "UniMessage[Union[TS1, Audio]]":
            """创建音频消息

            参数:
                id: 音频 ID
                url: 音频链接
                path: 音频路径
                raw: 音频原始数据
                mimetype: 音频 MIME 类型
                name: 音频名称
            返回:
                构建的消息
            """
            ...

        @classmethod
        def file(
            cls_or_self: Union["UniMessage[TS1]", type["UniMessage[TS1]"]],  # type: ignore
            id: Optional[str] = None,
            url: Optional[str] = None,
            path: Optional[Union[str, Path]] = None,
            raw: Optional[Union[bytes, BytesIO]] = None,
            mimetype: Optional[str] = None,
            name: str = "file.bin",
        ) -> "UniMessage[Union[TS1, File]]":
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
            cls_or_self: Union["UniMessage[TS1]", type["UniMessage[TS1]"]], id: str  # type: ignore
        ) -> "UniMessage[Union[TS1, Reply]]":
            """创建回复消息

            参数:
                id: 回复消息 ID

            返回:
                构建的消息
            """
            ...

        @classmethod
        def hyper(
            cls_or_self: Union["UniMessage[TS1]", type["UniMessage[TS1]"]],  # type: ignore
            flag: Literal["xml", "json"],
            content: str,
        ) -> "UniMessage[Union[TS1, Hyper]]":
            """创建卡片消息

            参数:
                flag: 卡片类型
                content: 卡片内容

            返回:
                构建的消息
            """
            ...

        @classmethod
        def i18n(
            cls_or_self: Union["UniMessage[TS1]", type["UniMessage[TS1]"]],  # type: ignore
            item_or_scope: Union[LangItem, str],
            type_: Optional[str] = None,
            /,
            *args,
            mapping: Optional[dict] = None,
            **kwargs,
        ) -> "UniMessage[Union[TS1, I18n]]":
            """创建 i18n 消息"""
            ...

    else:

        @_method
        def text(cls_or_self, text: str) -> "UniMessage[Union[TS1, Text]]":
            if isinstance(cls_or_self, UniMessage):
                cls_or_self.append(Text(text))
                return cls_or_self
            return UniMessage(Text(text))

        @_method
        def at(cls_or_self, user_id: str) -> "UniMessage[Union[TS1, At]]":
            if isinstance(cls_or_self, UniMessage):
                cls_or_self.append(At("user", user_id))
                return cls_or_self
            return UniMessage(At("user", user_id))

        @_method
        def at_role(cls_or_self, role_id: str) -> "UniMessage[Union[TS1, At]]":
            if isinstance(cls_or_self, UniMessage):
                cls_or_self.append(At("role", role_id))
                return cls_or_self
            return UniMessage(At("role", role_id))

        @_method
        def at_channel(cls_or_self, channel_id: str) -> "UniMessage[Union[TS1, At]]":
            if isinstance(cls_or_self, UniMessage):
                cls_or_self.append(At("channel", channel_id))
                return cls_or_self
            return UniMessage(At("channel", channel_id))

        @_method
        def at_all(cls_or_self, online: bool = False) -> "UniMessage[Union[TS1, AtAll]]":
            if isinstance(cls_or_self, UniMessage):
                cls_or_self.append(AtAll(online))
                return cls_or_self
            return UniMessage(AtAll(online))

        @_method
        def emoji(cls_or_self, id: str, name: Optional[str] = None) -> "UniMessage[Union[TS1, Emoji]]":
            if isinstance(cls_or_self, UniMessage):
                cls_or_self.append(Emoji(id, name))
                return cls_or_self
            return UniMessage(Emoji(id, name))

        @_method
        def image(
            cls_or_self,
            id: Optional[str] = None,
            url: Optional[str] = None,
            path: Optional[Union[str, Path]] = None,
            raw: Optional[Union[bytes, BytesIO]] = None,
            mimetype: Optional[str] = None,
            name: str = "image.png",
        ) -> "UniMessage[Union[TS1, Image]]":
            if isinstance(cls_or_self, UniMessage):
                cls_or_self.append(Image(id, url, path, raw, mimetype, name))
                return cls_or_self
            return UniMessage(Image(id, url, path, raw, mimetype, name))

        @_method
        def video(
            cls_or_self,
            id: Optional[str] = None,
            url: Optional[str] = None,
            path: Optional[Union[str, Path]] = None,
            raw: Optional[Union[bytes, BytesIO]] = None,
            mimetype: Optional[str] = None,
            name: str = "video.mp4",
        ) -> "UniMessage[Union[TS1, Video]]":
            if isinstance(cls_or_self, UniMessage):
                cls_or_self.append(Video(id, url, path, raw, mimetype, name))
                return cls_or_self
            return UniMessage(Video(id, url, path, raw, mimetype, name))

        @_method
        def voice(
            cls_or_self,
            id: Optional[str] = None,
            url: Optional[str] = None,
            path: Optional[Union[str, Path]] = None,
            raw: Optional[Union[bytes, BytesIO]] = None,
            mimetype: Optional[str] = None,
            name: str = "voice.wav",
        ) -> "UniMessage[Union[TS1, Voice]]":
            if isinstance(cls_or_self, UniMessage):
                cls_or_self.append(Voice(id, url, path, raw, mimetype, name))
                return cls_or_self
            return UniMessage(Voice(id, url, path, raw, mimetype, name))

        @_method
        def audio(
            cls_or_self,
            id: Optional[str] = None,
            url: Optional[str] = None,
            path: Optional[Union[str, Path]] = None,
            raw: Optional[Union[bytes, BytesIO]] = None,
            mimetype: Optional[str] = None,
            name: str = "audio.mp3",
        ) -> "UniMessage[Union[TS1, Audio]]":
            if isinstance(cls_or_self, UniMessage):
                cls_or_self.append(Audio(id, url, path, raw, mimetype, name))
                return cls_or_self
            return UniMessage(Audio(id, url, path, raw, mimetype, name))

        @_method
        def file(
            cls_or_self,
            id: Optional[str] = None,
            url: Optional[str] = None,
            path: Optional[Union[str, Path]] = None,
            raw: Optional[Union[bytes, BytesIO]] = None,
            mimetype: Optional[str] = None,
            name: str = "file.bin",
        ) -> "UniMessage[Union[TS1, File]]":
            if isinstance(cls_or_self, UniMessage):
                cls_or_self.append(File(id, url, path, raw, mimetype, name))
                return cls_or_self
            return UniMessage(File(id, url, path, raw, mimetype, name))

        @_method
        def reply(cls_or_self, id: str) -> "UniMessage[Union[TS1, Reply]]":
            if isinstance(cls_or_self, UniMessage):
                cls_or_self.append(Reply(id))
                return cls_or_self
            return UniMessage(Reply(id))

        @_method
        def hyper(cls_or_self, flag: Literal["xml", "json"], content: str) -> "UniMessage[Union[TS1, Hyper]]":
            if isinstance(cls_or_self, UniMessage):
                cls_or_self.append(Hyper(flag, content))
                return cls_or_self
            return UniMessage(Hyper(flag, content))

        @_method
        def i18n(
            cls_or_self,
            item_or_scope: Union[LangItem, str],
            type_: Optional[str] = None,
            /,
            *args,
            mapping: Optional[dict] = None,
            **kwargs,
        ) -> "UniMessage[Union[TS1, I18n]]":
            if isinstance(cls_or_self, UniMessage):
                cls_or_self.append(I18n(item_or_scope, type_, *args, mapping=mapping, **kwargs))  # type: ignore
                return cls_or_self
            return UniMessage(I18n(item_or_scope, type_, *args, mapping=mapping, **kwargs))  # type: ignore

    def __init__(
        self: "UniMessage[Segment]",
        message: Union[Iterable[Union[str, TS]], str, TS, None] = None,
    ):
        super().__init__()
        if isinstance(message, str):
            self.__iadd__(Text(message), _merge=False)
        elif isinstance(message, Iterable):
            for i in message:
                self.__iadd__(Text(i) if isinstance(i, str) else i, _merge=False)
        elif isinstance(message, Segment):
            self.__iadd__(message, _merge=False)
        self.__merge_text__()

    def __str__(self) -> str:
        return "".join(str(seg) for seg in self)

    def __repr__(self) -> str:
        return "[" + ", ".join(repr(seg) for seg in self) + "]"

    @classmethod
    def template(cls, format_string: Union[str, "UniMessage"]) -> UniMessageTemplate:
        """创建消息模板。

        用法和 `str.format` 大致相同，支持以 `UniMessage` 对象作为消息模板并输出消息对象。
        并且提供了拓展的格式化控制符，可以通过 `Segment` 的实例化方法创建消息。

        参数:
            format_string: 格式化模板

        返回:
            消息格式化器
        """
        return UniMessageTemplate(format_string, cls)

    def __merge_text__(self) -> Self:
        if not self:
            return self
        result = []
        last = list.__getitem__(self, 0)
        for seg in list.__getitem__(self, slice(1, None)):
            if isinstance(seg, Text) and isinstance(last, Text):
                _len = len(last.text)
                last.text += seg.text
                for scale, styles in seg.styles.items():
                    last.styles[(scale[0] + _len, scale[1] + _len)] = styles[:]
            else:
                result.append(last)
                last = seg
        result.append(last)
        self.clear()
        self.extend(result)
        return self

    @overload
    def __add__(self, other: str) -> "UniMessage[Union[TS, Text]]": ...

    @overload
    def __add__(self, other: Union[TS, Iterable[TS]]) -> "UniMessage[TS]": ...

    @overload
    def __add__(self, other: Union[TS1, Iterable[TS1]]) -> "UniMessage[Union[TS, TS1]]": ...

    def __add__(self, other: Union[str, TS, TS1, Iterable[Union[TS, TS1]]]) -> "UniMessage":
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
    def __radd__(self, other: str) -> "UniMessage[Union[Text, TS]]": ...

    @overload
    def __radd__(self, other: Union[TS, Iterable[TS]]) -> "UniMessage[TS]": ...

    @overload
    def __radd__(self, other: Union[TS1, Iterable[TS1]]) -> "UniMessage[Union[TS1, TS]]": ...

    def __radd__(self, other: Union[str, TS1, Iterable[TS1]]) -> "UniMessage":
        result = UniMessage(other)
        return result + self

    def __iadd__(self, other: Union[str, TS, Iterable[TS]], _merge: bool = True) -> Self:
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
    def __getitem__(self, args: type[TS1]) -> "UniMessage[TS1]":
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
    def __getitem__(self, args: tuple[type[TS1], slice]) -> "UniMessage[TS1]":
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
    def __getitem__(self, args: slice) -> "UniMessage[TS]":
        """切片消息段

        参数:
            args: 切片

        返回:
            消息切片 `args`
        """

    def __getitem__(
        self,
        args: Union[
            type[TS1],
            tuple[type[TS1], int],
            tuple[type[TS1], slice],
            int,
            slice,
        ],
    ) -> Union[TS, TS1, "UniMessage[TS]", "UniMessage[TS1]"]:
        arg1, arg2 = args if isinstance(args, tuple) else (args, None)
        if isinstance(arg1, int) and arg2 is None:
            return super().__getitem__(arg1)
        if isinstance(arg1, slice) and arg2 is None:
            return UniMessage(super().__getitem__(arg1))
        if TYPE_CHECKING:
            assert not isinstance(arg1, (slice, int))
        if issubclass(arg1, Segment) and arg2 is None:
            return UniMessage(seg for seg in self if isinstance(seg, arg1))
        if issubclass(arg1, Segment) and isinstance(arg2, int):
            return [seg for seg in self if isinstance(seg, arg1)][arg2]
        if issubclass(arg1, Segment) and isinstance(arg2, slice):
            return UniMessage([seg for seg in self if isinstance(seg, arg1)][arg2])
        raise ValueError("Incorrect arguments to slice")  # pragma: no cover

    def __contains__(self, value: Union[str, Segment, type[Segment]]) -> bool:
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

    def has(self, value: Union[str, Segment, type[Segment]]) -> bool:
        """与 {ref}``__contains__` <nonebot.adapters.Message.__contains__>` 相同"""
        return value in self

    def index(self, value: Union[str, Segment, type[Segment]], *args: SupportsIndex) -> int:
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

    def get(self, type_: type[TS], count: Optional[int] = None) -> "UniMessage[TS]":
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

    def count(self, value: Union[type[Segment], str, Segment]) -> int:
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

    def only(self, value: Union[type[Segment], str, Segment]) -> bool:
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

    def join(self, iterable: Iterable[Union[TS1, "UniMessage[TS1]"]]) -> "UniMessage[Union[TS, TS1]]":
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

    def copy(self) -> "UniMessage[TS]":
        """深拷贝消息"""
        return deepcopy(self)

    def include(self, *types: type[Segment]) -> "UniMessage[TS]":
        """过滤消息

        参数:
            types: 包含的消息段类型

        返回:
            新构造的消息
        """
        return UniMessage(seg for seg in self if seg.__class__ in types)

    def exclude(self, *types: type[Segment]) -> "UniMessage[TS]":
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

    @staticmethod
    async def generate(
        *,
        message: Optional[Message] = None,
        event: Optional[Event] = None,
        bot: Optional[Bot] = None,
        adapter: Optional[str] = None,
    ):
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
        if not (fn := BUILDER_MAPPING.get(adapter)):
            raise SerializeFailed(lang.require("nbp-uniseg", "unsupported").format(adapter=adapter))
        result = UniMessage(fn.generate(message))
        if (event and bot) and (_reply := await fn.extract_reply(event, bot)):
            if result.has(Reply) and result.index(Reply) == 0:
                result.pop(0)
            result.insert(0, _reply)
        return result

    @staticmethod
    def generate_without_reply(
        *,
        message: Optional[Message] = None,
        event: Optional[Event] = None,
        bot: Optional[Bot] = None,
        adapter: Optional[str] = None,
    ):
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
        if not (fn := BUILDER_MAPPING.get(adapter)):
            raise SerializeFailed(lang.require("nbp-uniseg", "unsupported").format(adapter=adapter))
        return UniMessage(fn.generate(message))

    @staticmethod
    def get_message_id(event: Optional[Event] = None, bot: Optional[Bot] = None, adapter: Optional[str] = None) -> str:
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
        if fn := EXPORTER_MAPPING.get(adapter):
            return fn.get_message_id(event)
        raise SerializeFailed(lang.require("nbp-uniseg", "unsupported").format(adapter=adapter))

    @staticmethod
    def get_target(event: Optional[Event] = None, bot: Optional[Bot] = None, adapter: Optional[str] = None) -> Target:
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
        if fn := EXPORTER_MAPPING.get(adapter):
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

    async def export(self, bot: Optional[Bot] = None, fallback: bool = True) -> Message:
        if not bot:
            try:
                bot = current_bot.get()
            except LookupError as e:
                raise SerializeFailed(lang.require("nbp-uniseg", "bot_missing")) from e
        adapter = bot.adapter
        adapter_name = adapter.get_name()
        if self.has(I18n):
            extra = {}
            try:
                event = current_event.get()
                extra["$event"] = event
                extra["$target"] = self.get_target(event, bot)
                msg_id = UniMessage.get_message_id(event, bot)
                extra["$message_id"] = msg_id
            except (LookupError, NotImplementedError, SerializeFailed):
                pass
            self._handle_i18n(extra)
        try:
            if fn := EXPORTER_MAPPING.get(adapter_name):
                return await fn.export(self, bot, fallback)
            raise SerializeFailed(lang.require("nbp-uniseg", "unsupported").format(adapter=adapter_name))
        except SerializeFailed:
            if fallback:
                return FallbackMessage(str(self))
            raise

    async def send(
        self,
        target: Union[Event, Target, None] = None,
        bot: Optional[Bot] = None,
        fallback: bool = True,
        at_sender: Union[str, bool] = False,
        reply_to: Union[str, bool, Reply, None] = False,
    ) -> "Receipt":
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
        msg = await self.export(bot, fallback)
        adapter = bot.adapter
        adapter_name = adapter.get_name()
        if not (fn := EXPORTER_MAPPING.get(adapter_name)):
            raise SerializeFailed(lang.require("nbp-uniseg", "unsupported").format(adapter=adapter_name))
        res = await fn.send_to(target, bot, msg)
        return Receipt(bot, target, fn, res if isinstance(res, list) else [res])

    async def finish(
        self,
        target: Union[Event, Target, None] = None,
        bot: Optional[Bot] = None,
        fallback: bool = True,
        at_sender: Union[str, bool] = False,
        reply_to: Union[str, bool, Reply, None] = False,
    ) -> NoReturn:
        await self.send(target, bot, fallback, at_sender, reply_to)
        raise FinishedException


@dataclass
class Receipt:
    bot: Bot
    context: Union[Event, Target]
    exporter: MessageExporter
    msg_ids: list[Any]

    @property
    def recallable(self) -> bool:
        return self.exporter.__class__.recall != MessageExporter.recall

    @property
    def editable(self) -> bool:
        return self.exporter.__class__.edit != MessageExporter.edit

    def get_reply(self, index: int = -1) -> Union[Reply, None]:
        if not self.msg_ids:
            return
        try:
            msg_id = self.msg_ids[index]
        except IndexError:
            msg_id = self.msg_ids[0]
        if not msg_id:
            return
        try:
            return self.exporter.get_reply(msg_id)
        except NotImplementedError:
            return

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
            self.msg_ids.remove(msg_id)
            return self
        except NotImplementedError:
            return self

    async def edit(
        self,
        message: Union[UniMessage, str, Iterable[Union[str, Segment]], Segment],
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
            if res:
                if isinstance(res, list):
                    self.msg_ids.remove(msg_id)
                    self.msg_ids.extend(res)
                else:
                    self.msg_ids[index] = res
            return self
        except NotImplementedError:
            return self

    async def send(
        self,
        message: Union[UniMessage, str, Iterable[Union[str, Segment]], Segment],
        fallback: bool = True,
        at_sender: Union[str, bool] = False,
        reply_to: Union[str, bool, Reply, None] = False,
        delay: float = 0,
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
        msg = await self.exporter.export(message, self.bot, fallback)
        res = await self.exporter.send_to(self.context, self.bot, msg)
        self.msg_ids.extend(res if isinstance(res, list) else [res])
        return self

    async def reply(
        self,
        message: Union[UniMessage, str, Iterable[Union[str, Segment]], Segment],
        fallback: bool = True,
        at_sender: Union[str, bool] = False,
        index: int = -1,
        delay: float = 0,
    ):
        return await self.send(message, fallback, at_sender, self.get_reply(index), delay)

    async def finish(
        self,
        message: Union[UniMessage, str, Iterable[Union[str, Segment]], Segment],
        fallback: bool = True,
        at_sender: Union[str, bool] = False,
        reply_to: Union[str, bool, Reply, None] = False,
        delay: float = 0,
    ):
        await self.send(message, fallback, at_sender, reply_to, delay)
        raise FinishedException
