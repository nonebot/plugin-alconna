import inspect
from dataclasses import dataclass
from abc import ABCMeta, abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
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

from .segment import Other, Segment

if TYPE_CHECKING:
    from .message import UniMessage


TS = TypeVar("TS", bound=Segment)
TMS = TypeVar("TMS", bound=MessageSegment)


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


class SerializeFailed(Exception):
    ...


def export(func: Callable[[Any, TS, Bot], Awaitable[MessageSegment]]):
    sig = inspect.signature(func)
    func.__export_target__ = sig.parameters["seg"].annotation
    return func


class MessageExporter(Generic[TMS], metaclass=ABCMeta):
    _mapping: Dict[Type[Segment], Callable[[Segment, Bot], Awaitable[MessageSegment]]]
    segment_class: Type[TMS]

    @classmethod
    @abstractmethod
    def get_adapter(cls) -> str:
        ...

    @abstractmethod
    def get_message_type(self) -> Type[Message]:
        ...

    @abstractmethod
    def get_message_id(self, event: Event) -> str:
        ...

    def get_target(self, event: Event) -> Target:
        return Target(event.get_user_id())

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
        message = self.get_message_type()()
        self.segment_class = self.get_message_type().get_segment_class()
        for seg in source:
            seg_type = seg.__class__
            if seg_type in self._mapping:
                res = await self._mapping[seg_type](seg, bot)
                if isinstance(res, list):
                    message.extend(res)
                    break
                message.append(res)
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
    async def send_to(self, target: Target, bot: Bot, message: Message):
        raise NotImplementedError

    async def recall(self, mid: Any, bot: Bot, context: Union[Target, Event]):
        raise NotImplementedError

    async def edit(self, new: Message, mid: Any, bot: Bot, context: Union[Target, Event]):
        raise NotImplementedError
