from copy import deepcopy
from typing_extensions import Self, SupportsIndex
from typing import (
    TYPE_CHECKING,
    List,
    Type,
    Tuple,
    Union,
    TypeVar,
    Iterable,
    Optional,
    overload,
)

from nonebot.internal.adapter import Bot, Event, Message

from ..argv import FallbackMessage
from .export import MAPPING, SerializeFailed
from .segment import Text, Other, Reply, Segment, reply, segments

TS = TypeVar("TS", bound=Segment)
TS1 = TypeVar("TS1", bound=Segment)


async def reply_handle(event: Event, bot: Bot):
    adapter = bot.adapter
    adapter_name = adapter.get_name()
    if adapter_name == "Telegram":
        if TYPE_CHECKING:
            from nonebot.adapters.telegram.event import MessageEvent

            assert isinstance(event, MessageEvent)
        if event.reply_to_message:
            return Reply(
                event.reply_to_message,
                f"{event.reply_to_message.message_id}.{event.chat.id}",
                event.reply_to_message.original_message,
            )
    elif adapter_name == "Feishu":
        if TYPE_CHECKING:
            from nonebot.adapters.feishu.event import MessageEvent

            assert isinstance(event, MessageEvent)
        if event.reply:
            return Reply(event.reply, event.reply.message_id, event.reply.body.content)
    elif adapter_name == "ntchat":
        if TYPE_CHECKING:
            from nonebot.adapters.ntchat.event import QuoteMessageEvent

            assert isinstance(event, QuoteMessageEvent)
        if event.type == 11061:
            return Reply(event, event.quote_message_id)
    elif adapter_name == "QQ Guild":
        if TYPE_CHECKING:
            from nonebot.adapters.qqguild.event import MessageEvent

            assert isinstance(event, MessageEvent)
        if event.reply and event.reply.message:
            return Reply(
                event.reply.message,
                str(event.reply.message.id),
                event.reply.message.content,
            )
    elif adapter_name == "mirai2":
        if TYPE_CHECKING:
            from nonebot.adapters.mirai2.event import MessageEvent

            assert isinstance(event, MessageEvent)
        if event.quote:
            return Reply(event.quote, str(event.quote.id), event.quote.origin)
    elif adapter_name == "Kaiheila":
        if TYPE_CHECKING:
            from nonebot.adapters.kaiheila import Bot as KaiheilaBot
            from nonebot.adapters.kaiheila.event import MessageEvent

            assert isinstance(event, MessageEvent)
            assert isinstance(bot, KaiheilaBot)

        api = (
            "directMessage_view"
            if event.__event__ == "message.private"
            else "message_view"
        )
        message = await bot.call_api(
            api,
            msg_id=event.msg_id,
            **(
                {"chat_code": event.event.code}
                if event.__event__ == "message.private"
                else {}
            ),
        )
        if message.quote:
            return Reply(message.quote, message.quote.id_, None)
    elif adapter_name == "Discord":
        if TYPE_CHECKING:
            from nonebot.adapters.discord import MessageEvent

            assert isinstance(event, MessageEvent)

        if hasattr(event, "message_reference") and hasattr(
            event.message_reference, "message_id"
        ):
            return Reply(
                event.message_reference,  # type: ignore
                event.message_reference.message_id,  # type: ignore
                None,
            )

    elif _reply := getattr(event, "reply", None):
        return Reply(_reply, str(_reply.message_id), getattr(_reply, "message", None))
    return None


class UniMessage(List[TS]):
    """通用消息序列

    参数:
        message: 消息内容
    """

    def __init__(
        self: "UniMessage[Segment]",
        message: Union[Iterable[Union[str, TS]], str, TS, None] = None,
    ):
        super().__init__()
        if isinstance(message, str):
            self.append(Text(message))
        elif isinstance(message, Iterable):
            for i in message:
                self.append(Text(i) if isinstance(i, str) else i)
        elif isinstance(message, Segment):
            self.append(message)

    def __str__(self) -> str:
        return "".join(str(seg) for seg in self)

    def __repr__(self) -> str:
        return "".join(repr(seg) for seg in self)

    @overload
    def __add__(self, other: Union[str, TS, Iterable[TS]]) -> "UniMessage[TS]":
        ...

    @overload
    def __add__(
        self, other: Union[str, TS1, Iterable[TS1]]
    ) -> "UniMessage[Union[TS, TS1]]":
        ...

    def __add__(
        self, other: Union[str, TS, TS1, Iterable[Union[TS, TS1]]]
    ) -> "UniMessage[Union[TS, TS1]]":
        result = self.copy()
        if isinstance(other, str):
            result.append(Text(other))  # type: ignore
        elif isinstance(other, Segment):
            result.append(other)  # type: ignore
        elif isinstance(other, Iterable):
            result.extend(other)  # type: ignore
        else:
            raise TypeError(f"Unsupported type {type(other)!r}")
        return result  # type: ignore

    def __radd__(
        self, other: Union[str, TS1, Iterable[TS1]]
    ) -> "UniMessage[Union[TS, TS1]]":
        result = UniMessage(other)
        return result + self

    def __iadd__(self, other: Union[str, TS, Iterable[TS]]) -> Self:
        if isinstance(other, str):
            self.append(Text(other))  # type: ignore
        elif isinstance(other, Segment):
            self.append(other)
        elif isinstance(other, Iterable):
            self.extend(other)
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

    def __contains__(self, value: Union[Segment, Type[Segment]]) -> bool:
        """检查消息段是否存在

        参数:
            value: 消息段或消息段类型
        返回:
            消息内是否存在给定消息段或给定类型的消息段
        """
        if isinstance(value, type):
            return bool(next((seg for seg in self if isinstance(seg, value)), None))
        return super().__contains__(value)

    def has(self, value: Union[Segment, Type[Segment]]) -> bool:
        """与 {ref}``__contains__` <nonebot.adapters.Message.__contains__>` 相同"""
        return value in self

    def index(self, value: Union[Segment, Type[Segment]], *args: SupportsIndex) -> int:
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

        iterator, filtered = (
            seg for seg in self if isinstance(seg, type_)
        ), UniMessage()
        for _ in range(count):
            seg = next(iterator, None)
            if seg is None:
                break
            filtered.append(seg)
        return filtered

    def count(self, value: Union[Type[Segment], Segment]) -> int:
        """计算指定消息段的个数

        参数:
            value: 消息段或消息段类型

        返回:
            个数
        """
        return (
            len(self[value])  # type: ignore
            if isinstance(value, type)
            else super().count(value)  # type: ignore
        )

    def only(self, value: Union[Type[Segment], Segment]) -> bool:
        """检查消息中是否仅包含指定消息段

        参数:
            value: 指定消息段或消息段类型

        返回:
            是否仅包含指定消息段
        """
        if isinstance(value, type):
            return all(isinstance(seg, value) for seg in self)
        return all(seg == value for seg in self)

    def join(
        self, iterable: Iterable[Union[TS1, "UniMessage[TS1]"]]
    ) -> "UniMessage[Union[TS, TS1]]":
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
            if isinstance(msg, (str, Segment)):
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

        return "".join(seg for seg in self if isinstance(seg, str))

    @staticmethod
    async def generate(event: Event, bot: Bot):
        try:
            msg = event.get_message()
        except Exception:
            return UniMessage()
        result = UniMessage()
        msg_copy = msg.copy()
        if _reply := await reply_handle(event, bot):
            result.append(_reply)
        elif (res := reply.validate(msg[0])).success:
            result.append(res.value)
            msg_copy.pop(0)
        for seg in msg_copy:
            for pat in segments:
                if (res := pat.validate(seg)).success:
                    result.append(res.value)
                    break
            else:
                result.append(Other(seg))
        return result

    async def export(self, bot: Bot, fallback: bool = True) -> Message:
        adapter = bot.adapter
        adapter_name = adapter.get_name()
        if fn := MAPPING.get(adapter_name):
            return await fn(self, bot, fallback)
        if fallback:
            return FallbackMessage(str(self))
        raise SerializeFailed(f"Can not export message to {adapter_name} message")
