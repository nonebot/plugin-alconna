from io import BytesIO
from pathlib import Path
from copy import deepcopy
from types import FunctionType
from typing_extensions import Self, SupportsIndex
from typing import TYPE_CHECKING, List, Type, Tuple, Union, Literal, TypeVar, Iterable, Optional, overload

from tarina import lang
from nonebot.internal.adapter import Bot, Event, Message
from nonebot.internal.matcher import current_bot, current_event

from .receipt import Receipt
from .adapters import MAPPING
from .fallback import FallbackMessage
from .template import UniMessageTemplate
from .export import Target, SerializeFailed
from .segment import (
    At,
    Card,
    File,
    Text,
    AtAll,
    Audio,
    Emoji,
    Image,
    Other,
    Reply,
    Video,
    Voice,
    Segment,
    reply,
    segments,
    reply_handle,
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


class UniMessage(List[TS]):
    """通用消息序列

    参数:
        message: 消息内容
    """

    if TYPE_CHECKING:

        @classmethod
        def text(
            cls_or_self: Union["UniMessage[TS1]", Type["UniMessage[TS1]"]], text: str  # type: ignore
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
            cls_or_self: Union["UniMessage[TS1]", Type["UniMessage[TS1]"]], user_id: str  # type: ignore
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
            cls_or_self: Union["UniMessage[TS1]", Type["UniMessage[TS1]"]], role_id: str  # type: ignore
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
            cls_or_self: Union["UniMessage[TS1]", Type["UniMessage[TS1]"]], channel_id: str  # type: ignore
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
            cls_or_self: Union["UniMessage[TS1]", Type["UniMessage[TS1]"]],  # type: ignore
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
            cls_or_self: Union["UniMessage[TS1]", Type["UniMessage[TS1]"]],  # type: ignore
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
            cls_or_self: Union["UniMessage[TS1]", Type["UniMessage[TS1]"]],  # type: ignore
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
            cls_or_self: Union["UniMessage[TS1]", Type["UniMessage[TS1]"]],  # type: ignore
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
            cls_or_self: Union["UniMessage[TS1]", Type["UniMessage[TS1]"]],  # type: ignore
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
            cls_or_self: Union["UniMessage[TS1]", Type["UniMessage[TS1]"]],  # type: ignore
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
            cls_or_self: Union["UniMessage[TS1]", Type["UniMessage[TS1]"]],  # type: ignore
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
            cls_or_self: Union["UniMessage[TS1]", Type["UniMessage[TS1]"]], id: str  # type: ignore
        ) -> "UniMessage[Union[TS1, Reply]]":
            """创建回复消息

            参数:
                id: 回复消息 ID

            返回:
                构建的消息
            """
            ...

        @classmethod
        def card(
            cls_or_self: Union["UniMessage[TS1]", Type["UniMessage[TS1]"]],  # type: ignore
            flag: Literal["xml", "json"],
            content: str,
        ) -> "UniMessage[Union[TS1, Card]]":
            """创建卡片消息

            参数:
                flag: 卡片类型
                content: 卡片内容

            返回:
                构建的消息
            """
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
        def card(cls_or_self, flag: Literal["xml", "json"], content: str) -> "UniMessage[Union[TS1, Card]]":
            if isinstance(cls_or_self, UniMessage):
                cls_or_self.append(Card(flag, content))
                return cls_or_self
            return UniMessage(Card(flag, content))

    def __init__(
        self: "UniMessage[Segment]",
        message: Union[Iterable[Union[str, TS]], str, TS, None] = None,
    ):
        super().__init__()
        if isinstance(message, str):
            self.__iadd__(Text(message))
        elif isinstance(message, Iterable):
            for i in message:
                self.__iadd__(Text(i) if isinstance(i, str) else i)
        elif isinstance(message, Segment):
            self.__iadd__(message)

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

    @overload
    def __add__(self, other: str) -> "UniMessage[Union[TS, Text]]":
        ...

    @overload
    def __add__(self, other: Union[TS, Iterable[TS]]) -> "UniMessage[TS]":
        ...

    @overload
    def __add__(self, other: Union[TS1, Iterable[TS1]]) -> "UniMessage[Union[TS, TS1]]":
        ...

    def __add__(self, other: Union[str, TS, TS1, Iterable[Union[TS, TS1]]]) -> "UniMessage":
        result: UniMessage = self.copy()
        if isinstance(other, str):
            if result and isinstance(text := result[-1], Text):
                text.text += other
            else:
                result.append(Text(other))
        elif isinstance(other, Segment):
            if result and isinstance(result[-1], Text) and isinstance(other, Text):
                result[-1] = Text(result[-1].text + other.text)
            else:
                result.append(other)
        elif isinstance(other, Iterable):
            for seg in other:
                result += seg
        else:
            raise TypeError(f"Unsupported type {type(other)!r}")
        return result

    @overload
    def __radd__(self, other: str) -> "UniMessage[Union[Text, TS]]":
        ...

    @overload
    def __radd__(self, other: Union[TS, Iterable[TS]]) -> "UniMessage[TS]":
        ...

    @overload
    def __radd__(self, other: Union[TS1, Iterable[TS1]]) -> "UniMessage[Union[TS1, TS]]":
        ...

    def __radd__(self, other: Union[str, TS1, Iterable[TS1]]) -> "UniMessage":
        result = UniMessage(other)
        return result + self

    def __iadd__(self, other: Union[str, TS, Iterable[TS]]) -> Self:
        if isinstance(other, str):
            if self and isinstance(text := self[-1], Text):
                text.text += other
            else:
                self.append(Text(other))  # type: ignore
        elif isinstance(other, Segment):
            if self and (isinstance(text := self[-1], Text) and isinstance(other, Text)):
                text.text += other.text
            else:
                self.append(other)
        elif isinstance(other, Iterable):
            for seg in other:
                self.__iadd__(seg)
        else:
            raise TypeError(f"Unsupported type {type(other)!r}")
        return self

    @overload
    def __getitem__(self, args: Type[TS1]) -> "UniMessage[TS1]":
        """获取仅包含指定消息段类型的消息

        参数:
            args: 消息段类型

        返回:
            所有类型为 `args` 的消息段
        """

    @overload
    def __getitem__(self, args: Tuple[Type[TS1], int]) -> TS1:
        """索引指定类型的消息段

        参数:
            args: 消息段类型和索引

        返回:
            类型为 `args[0]` 的消息段第 `args[1]` 个
        """

    @overload
    def __getitem__(self, args: Tuple[Type[TS1], slice]) -> "UniMessage[TS1]":
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
    def __getitem__(self, args: slice) -> Self:
        """切片消息段

        参数:
            args: 切片

        返回:
            消息切片 `args`
        """

    def __getitem__(
        self,
        args: Union[
            Type[TS1],
            Tuple[Type[TS1], int],
            Tuple[Type[TS1], slice],
            int,
            slice,
        ],
    ) -> Union[TS, TS1, "UniMessage[TS1]", Self]:
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

    def __contains__(self, value: Union[str, Segment, Type[Segment]]) -> bool:
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

    def has(self, value: Union[str, Segment, Type[Segment]]) -> bool:
        """与 {ref}``__contains__` <nonebot.adapters.Message.__contains__>` 相同"""
        return value in self

    def index(self, value: Union[str, Segment, Type[Segment]], *args: SupportsIndex) -> int:
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

    def get(self, type_: Type[TS], count: Optional[int] = None) -> "UniMessage[TS]":
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
        return filtered

    def count(self, value: Union[Type[Segment], str, Segment]) -> int:
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

    def only(self, value: Union[Type[Segment], str, Segment]) -> bool:
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
        return ret

    def copy(self) -> "UniMessage[TS]":
        """深拷贝消息"""
        return deepcopy(self)

    def include(self, *types: Type[Segment]) -> Self:
        """过滤消息

        参数:
            types: 包含的消息段类型

        返回:
            新构造的消息
        """
        return UniMessage(seg for seg in self if seg.__class__ in types)

    def exclude(self, *types: Type[Segment]) -> Self:
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
        *, message: Optional[Message] = None, event: Optional[Event] = None, bot: Optional[Bot] = None
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
        result = UniMessage()
        msg_copy = message.copy()
        if (event and bot) and (_reply := await reply_handle(event, bot)):
            result.append(_reply)
        elif (res := reply.validate(message[0])).success:
            res.value.origin = message[0]
            result.append(res.value)
            msg_copy.pop(0)
        for seg in msg_copy:
            for pat in segments:
                if (res := pat.validate(seg)).success:
                    res.value.origin = seg
                    result.append(res.value)
                    break
            else:
                result.append(Other(seg))
        return result

    @staticmethod
    def get_message_id(
        event: Optional[Event] = None, bot: Optional[Bot] = None, adapter: Optional[str] = None
    ) -> str:
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
        if fn := MAPPING.get(adapter):
            return fn.get_message_id(event)
        raise SerializeFailed(lang.require("nbp-uniseg", "unsupported").format(adapter=adapter))

    @staticmethod
    def get_target(
        event: Optional[Event] = None, bot: Optional[Bot] = None, adapter: Optional[str] = None
    ) -> Target:
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
        if fn := MAPPING.get(adapter):
            return fn.get_target(event)
        raise SerializeFailed(lang.require("nbp-uniseg", "unsupported").format(adapter=adapter))

    async def export(self, bot: Optional[Bot] = None, fallback: bool = True) -> Message:
        if not bot:
            try:
                bot = current_bot.get()
            except LookupError as e:
                raise SerializeFailed(lang.require("nbp-uniseg", "bot_missing")) from e
        adapter = bot.adapter
        adapter_name = adapter.get_name()
        try:
            if fn := MAPPING.get(adapter_name):
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
        reply_to: Union[str, bool] = False,
    ) -> Receipt:
        if not bot:
            try:
                bot = current_bot.get()
            except LookupError as e:
                raise SerializeFailed(lang.require("nbp-uniseg", "bot_missing")) from e
        if not target:
            try:
                target = current_event.get()
            except LookupError as e:
                raise SerializeFailed(lang.require("nbp-uniseg", "event_missing")) from e
        if at_sender:
            if isinstance(at_sender, str):
                self.insert(0, At("user", at_sender))  # type: ignore
            elif isinstance(target, Event):
                self.insert(0, At("user", target.get_user_id()))  # type: ignore
            else:
                raise TypeError("at_sender must be str when target is not Event")
        if reply_to:
            if isinstance(reply_to, bool):
                if isinstance(target, Event):
                    reply_to = self.get_message_id(target, bot)
                else:
                    raise TypeError("reply_to must be str when target is not Event")
            self.insert(0, Reply(reply_to))  # type: ignore
        msg = await self.export(bot, fallback)
        adapter = bot.adapter
        adapter_name = adapter.get_name()
        if not (fn := MAPPING.get(adapter_name)):
            raise SerializeFailed(lang.require("nbp-uniseg", "unsupported").format(adapter=adapter_name))
        if isinstance(target, Event):
            _target = fn.get_target(target)
            try:
                res = await fn.send_to(_target, bot, msg)
            except (AssertionError, NotImplementedError):
                res = await bot.send(target, msg)
        else:
            res = await fn.send_to(target, bot, msg)
        return Receipt(bot, target, fn, res if isinstance(res, list) else [res])
