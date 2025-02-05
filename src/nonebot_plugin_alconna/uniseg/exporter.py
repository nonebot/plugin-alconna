import inspect
from abc import ABCMeta, abstractmethod
from collections.abc import Sequence, Awaitable
from typing import Any, Union, Generic, TypeVar, Callable, get_args, overload, get_origin

from tarina import lang
from nonebot.adapters import Bot, Event, Message, MessageSegment

from .target import Target as Target
from .fallback import FallbackStrategy
from .constraint import SupportAdapter, SerializeFailed
from .segment import (
    At,
    Text,
    AtAll,
    Emoji,
    Hyper,
    Media,
    Other,
    Reply,
    Button,
    Segment,
    Keyboard,
    Reference,
    CustomNode,
    custom,
)

TS = TypeVar("TS", bound=Segment)
TM = TypeVar("TM", bound=Message)
TMS = TypeVar("TMS", bound=MessageSegment, covariant=True)


def merge_text(msg: Message) -> Message:
    if not msg:
        return msg
    result = []
    last = list.__getitem__(msg, 0)
    for seg in list.__getitem__(msg, slice(1, None)):
        if seg.is_text() and last.is_text() and seg.type == "text" and len(seg.data) == 1:
            last.data["text"] += seg.data["text"]
        else:
            result.append(last)
            last = seg
    result.append(last)
    msg.clear()
    msg.extend(result)
    return msg


async def _auto_fallback(seg: Segment, bot: Union[Bot, None]):
    if isinstance(seg, Media):
        if seg.url:
            return [Text(f"[{seg.type}]{seg.url} ")]
        if seg.__class__.to_url and seg.raw:
            url = await seg.__class__.to_url(seg.raw, bot, None if seg.name == seg.__default_name__ else seg.name)
            return [Text(f"[{seg.type}]{url} ")]
        if seg.__class__.to_url and seg.path:
            url = await seg.__class__.to_url(seg.path, bot, None if seg.name == seg.__default_name__ else seg.name)
            return [Text(f"[{seg.type}]{url} ")]
        return [Text(f"[{seg.type}]{'' if seg.name == seg.__default_name__ else seg.name} ")]
    if isinstance(seg, At):
        if seg.flag == "channel":
            return [Text(f"#{seg.display or seg.target} ")]
        return [Text(f"@{seg.display or seg.target} ")]
    if isinstance(seg, AtAll):
        return [Text("@全体成员 ")]
    if isinstance(seg, Emoji):
        return [Text(f"[{seg.name}]")] if seg.name else [Text(f"[表情:{seg.id}]")]
    if isinstance(seg, Hyper):
        return [Text(f"[{seg.format}]")]
    if isinstance(seg, Reply):
        return []  # Text(f"> 回复{seg.msg or seg.id}的消息\n")]
    if isinstance(seg, Button):
        if seg.flag == "link":
            return [Text(f"[{seg.label}]({seg.url})")]
        if seg.flag != "action":
            return [Text(f"[{seg.label}]{seg.text} ")]
        return [Text(f"[{seg.label}]")]
    if isinstance(seg, Keyboard):
        if seg.children:
            msg = []
            for but in seg.children:
                msg.extend(await _auto_fallback(but, bot))
            return msg
        return []  # Text("[keyboard]")]
    if isinstance(seg, Reference):
        if not seg.children:
            return []  # [Text(f"> msg:{seg.id}\n")]
        msg = []
        for node in seg.children:
            if isinstance(node, CustomNode):
                if isinstance(node.content, str):
                    msg.append(Text(node.content))
                else:
                    msg.extend(node.content)
            else:
                msg.append(Text(f"> msg:{node.id}"))
        return msg
    return [Text(str(seg))]


@overload
def export(
    func: Callable[[Any, TS, Union[Bot, None]], Awaitable[TMS]],
) -> Callable[[Any, TS, Union[Bot, None]], Awaitable[TMS]]: ...


@overload
def export(
    func: Callable[[Any, TS, Union[Bot, None]], Awaitable[list[TMS]]],
) -> Callable[[Any, TS, Union[Bot, None]], Awaitable[list[TMS]]]: ...


@overload
def export(
    func: Callable[[Any, TS, Union[Bot, None]], Awaitable[Union[TMS, list[TMS]]]],
) -> Callable[[Any, TS, Union[Bot, None]], Awaitable[Union[TMS, list[TMS]]]]: ...


def export(
    func: Union[
        Callable[[Any, TS, Union[Bot, None]], Awaitable[TMS]],
        Callable[[Any, TS, Union[Bot, None]], Awaitable[list[TMS]]],
        Callable[[Any, TS, Union[Bot, None]], Awaitable[Union[TMS, list[TMS]]]],
    ],
):
    sig = inspect.signature(func)
    func.__export_target__ = sig.parameters["seg"].annotation
    return func


class MessageExporter(Generic[TM], metaclass=ABCMeta):
    _mapping: dict[
        type[Segment],
        Union[
            Callable[[Segment, Union[Bot, None]], Awaitable[MessageSegment]],
            Callable[[Segment, Union[Bot, None]], Awaitable[list[MessageSegment]]],
            Callable[[Segment, Union[Bot, None]], Awaitable[Union[MessageSegment, list[MessageSegment]]]],
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

    async def export(self, source: Sequence[Segment], bot: Union[Bot, None], fallback: Union[bool, FallbackStrategy]):
        msg_type = self.get_message_type()
        message = msg_type([])
        for seg in source:
            seg_type = seg.__class__
            if seg_type in self._mapping:
                try:
                    res = await self._mapping[seg_type](seg, bot)
                    if isinstance(res, list):
                        message.extend(res)
                    else:
                        message.append(res)
                    continue
                except (SerializeFailed, NotImplementedError):
                    pass
            if res := await custom.export(self, seg, bot, fallback):  # type: ignore
                if isinstance(res, list):
                    message.extend(res)
                else:
                    message.append(res)
                continue
            if isinstance(seg, Other):
                message.append(seg.origin)  # type: ignore
            elif bot and bot.adapter.get_name() == SupportAdapter.nonebug:
                message += str(seg)
            elif isinstance(fallback, FallbackStrategy) and fallback != FallbackStrategy.forbid:
                if fallback == FallbackStrategy.ignore:
                    continue
                if fallback == FallbackStrategy.to_text:
                    message += str(seg)
                elif fallback == FallbackStrategy.rollback:
                    if not seg.children:
                        if isinstance(seg, Media):
                            if seg.url:
                                message += f"[{seg.type}]{seg.url}"
                            else:
                                message += f"[{seg.type}]{'' if seg.name == seg.__default_name__ else seg.name}"
                        else:
                            message += str(seg)
                    elif isinstance(seg, Reference):
                        for node in seg.children:
                            if isinstance(node, CustomNode):
                                if isinstance(node.content, str):
                                    message.append(msg_type(node.content))
                                else:
                                    message.extend(await self.export(node.content, bot, FallbackStrategy.auto))
                            else:
                                message += f"> msg:{node.id}\n"
                    else:
                        message.extend(await self.export(seg.children, bot, fallback))
                elif seg.children:
                    message.extend(await self.export(seg.children, bot, FallbackStrategy.auto))
                else:
                    message.extend(await self.export((await _auto_fallback(seg, bot)), bot, FallbackStrategy.auto))
            elif fallback is True:
                if seg.children:
                    message.extend(await self.export(seg.children, bot, FallbackStrategy.auto))
                else:
                    message.extend(await self.export((await _auto_fallback(seg, bot)), bot, FallbackStrategy.auto))
            else:
                raise SerializeFailed(
                    lang.require("nbp-uniseg", "failed").format(
                        target=seg, adapter=bot.adapter.get_name() if bot else "Unknown"
                    )
                )

        return merge_text(message)

    @abstractmethod
    async def send_to(self, target: Union[Target, Event], bot: Bot, message: Message, **kwargs):
        raise NotImplementedError

    async def recall(self, mid: Any, bot: Bot, context: Union[Target, Event]):
        raise NotImplementedError

    async def edit(self, new: Message, mid: Any, bot: Bot, context: Union[Target, Event]):
        raise NotImplementedError

    def get_reply(self, mid: Any):
        raise NotImplementedError
