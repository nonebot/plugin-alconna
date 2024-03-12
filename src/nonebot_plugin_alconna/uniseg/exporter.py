import inspect
from abc import ABCMeta, abstractmethod
from dataclasses import field, dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Type,
    Union,
    Generic,
    TypeVar,
    Callable,
    Awaitable,
    get_args,
    get_origin,
)

from tarina import lang
from nonebot.adapters import Bot, Event, Message, MessageSegment

from .segment import Other, Reply, Custom, Segment
from .constraint import SupportAdapter, SerializeFailed

if TYPE_CHECKING:
    from .message import UniMessage


TS = TypeVar("TS", bound=Segment)
TM = TypeVar("TM", bound=Message)


@dataclass
class Target:
    id: str
    """目标id；若为群聊则为group_id或者channel_id，若为私聊则为user_id"""
    parent_id: str = ""
    """父级id；若为频道则为guild_id，其他情况为空字符串"""
    channel: bool = False
    """是否为频道，仅当目标平台符合频道概念时"""
    private: bool = False
    """是否为私聊"""
    source: str = ""
    """可能的事件id"""
    platform: Union[str, None] = None
    """平台(适配器)名称，若为None则需要明确指定 Bot 对象"""
    self_id: Union[str, None] = None
    """机器人id，若为None则需要明确指定 Bot 对象"""
    extra: Dict[str, Any] = field(default_factory=dict)
    """额外信息，用于适配器扩展"""

    async def send(
        self,
        message: Union[str, Message, "UniMessage"],
        bot: Union[Bot, None] = None,
        fallback: bool = True,
        at_sender: Union[str, bool] = False,
        reply_to: Union[str, bool, Reply, None] = False,
    ):
        """发送消息"""
        if isinstance(message, str):
            from .message import UniMessage

            message = UniMessage(message)
        if isinstance(message, Message):
            from .message import UniMessage

            message = await UniMessage.generate(message=message, bot=bot)
        return await message.send(self, bot, fallback, at_sender, reply_to)


def export(
    func: Union[
        Callable[[Any, TS, Bot], Awaitable[MessageSegment]], Callable[[Any, TS, Bot], Awaitable[List[MessageSegment]]]
    ]
):
    sig = inspect.signature(func)
    func.__export_target__ = sig.parameters["seg"].annotation
    return func


class MessageExporter(Generic[TM], metaclass=ABCMeta):
    _mapping: Dict[
        Type[Segment],
        Union[
            Callable[[Segment, Bot], Awaitable[MessageSegment]],
            Callable[[Segment, Bot], Awaitable[List[MessageSegment]]],
        ],
    ]

    @classmethod
    @abstractmethod
    def get_adapter(cls) -> SupportAdapter: ...

    @abstractmethod
    def get_message_type(self) -> Type[TM]: ...

    @abstractmethod
    def get_message_id(self, event: Event) -> str: ...

    def get_target(self, event: Event, bot: Union[Bot, None] = None) -> Target:
        return Target(event.get_user_id(), platform=self.get_adapter(), self_id=bot.self_id if bot else None)

    def __init__(self):
        self._mapping = {}
        for attr in self.__class__.__dict__.values():
            if callable(attr) and hasattr(attr, "__export_target__"):
                method = getattr(self, attr.__name__)
                target = attr.__export_target__
                if get_origin(target) is Union:
                    for t in get_args(target):
                        self._mapping[t] = method
                else:
                    self._mapping[target] = method

    async def export(self, source: "UniMessage", bot: Bot, fallback: bool):
        msg_type = self.get_message_type()
        message = msg_type()
        for seg in source:
            seg_type = seg.__class__
            if seg_type in self._mapping:
                res = await self._mapping[seg_type](seg, bot)
                if isinstance(res, list):
                    message.extend(res)
                else:
                    message.append(res)
            elif isinstance(seg, Custom):
                message.append(seg.export(msg_type))
            elif isinstance(seg, Other):
                message.append(seg.origin)  # type: ignore
            elif fallback:
                message += str(seg)
            else:
                raise SerializeFailed(
                    lang.require("nbp-uniseg", "failed").format(target=seg, adapter=bot.adapter.get_name())
                )
        return message

    @abstractmethod
    async def send_to(self, target: Union[Target, Event], bot: Bot, message: Message):
        raise NotImplementedError

    async def recall(self, mid: Any, bot: Bot, context: Union[Target, Event]):
        raise NotImplementedError

    async def edit(self, new: Message, mid: Any, bot: Bot, context: Union[Target, Event]):
        raise NotImplementedError

    def get_reply(self, mid: Any):
        raise NotImplementedError
