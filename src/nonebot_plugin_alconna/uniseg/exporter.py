import inspect
from collections.abc import Awaitable
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any, Union, Generic, TypeVar, Callable, get_args, get_origin

from tarina import lang
from nonebot.adapters import Bot, Event, Message, MessageSegment

from .target import Target as Target
from .segment import Other, Segment, custom
from .constraint import SupportAdapter, SerializeFailed

if TYPE_CHECKING:
    from .message import UniMessage


TS = TypeVar("TS", bound=Segment)
TM = TypeVar("TM", bound=Message)


def export(
    func: Union[
        Callable[[Any, TS, Bot], Awaitable[MessageSegment]], Callable[[Any, TS, Bot], Awaitable[list[MessageSegment]]]
    ]
):
    sig = inspect.signature(func)
    func.__export_target__ = sig.parameters["seg"].annotation
    return func


class MessageExporter(Generic[TM], metaclass=ABCMeta):
    _mapping: dict[
        type[Segment],
        Union[
            Callable[[Segment, Bot], Awaitable[MessageSegment]],
            Callable[[Segment, Bot], Awaitable[list[MessageSegment]]],
        ],
    ]

    @classmethod
    @abstractmethod
    def get_adapter(cls) -> SupportAdapter: ...

    @abstractmethod
    def get_message_type(self) -> type[TM]: ...

    @abstractmethod
    def get_message_id(self, event: Event) -> str: ...

    def get_target(self, event: Event, bot: Union[Bot, None] = None) -> Target:
        return Target(event.get_user_id(), adapter=self.get_adapter(), self_id=bot.self_id if bot else None)

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
        message = msg_type([])
        for seg in source:
            seg_type = seg.__class__
            if seg_type in self._mapping:
                res = await self._mapping[seg_type](seg, bot)
                if isinstance(res, list):
                    message.extend(res)
                else:
                    message.append(res)
            elif res := await custom.export(self, seg, bot, fallback):  # type: ignore
                if isinstance(res, list):
                    message.extend(res)
                else:
                    message.append(res)
            elif isinstance(seg, Other):
                message.append(seg.origin)  # type: ignore
            elif fallback or bot.adapter.get_name() == SupportAdapter.nonebug:
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
