import inspect
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
from nonebot.adapters import Bot, Message, MessageSegment

from .segment import Other, Segment

if TYPE_CHECKING:
    from .message import UniMessage


TS = TypeVar("TS", bound=Segment)
TMS = TypeVar("TMS", bound=MessageSegment)


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

    async def __call__(self, source: "UniMessage", bot: Bot, fallback: bool):
        message = self.get_message_type()()
        self.segment_class = self.get_message_type().get_segment_class()
        for seg in source:
            seg_type = seg.__class__
            if seg_type in self._mapping:
                message.append(await self._mapping[seg_type](seg, bot))
            elif isinstance(seg, Other):
                message.append(seg.origin)  # type: ignore
            elif fallback:
                message += str(seg)
            else:
                raise SerializeFailed(
                    lang.require("nbp-uniseg", "failed").format(target=seg, adapter=bot.adapter.get_name())
                )
        return message
