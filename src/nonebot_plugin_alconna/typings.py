from __future__ import annotations

from typing_extensions import Self, ParamSpec, TypeAlias
from typing import Any, Union, Generic, TypeVar, Callable, Awaitable

from tarina import lang
from arclet.alconna import Arparma
from nonebot.typing import T_State
from nepattern import MatchMode, BasePattern, MatchFailed
from nonebot.internal.adapter import Bot, Event, Message, MessageSegment

from .uniseg import Segment, UniMessage

T = TypeVar("T")
TMS = TypeVar("TMS", bound=MessageSegment)
TCallable = TypeVar("TCallable", bound=Callable[..., Any])
P = ParamSpec("P")


class SegmentPattern(BasePattern[TMS, MessageSegment], Generic[TMS, P]):
    def __init__(
        self,
        name: str,
        origin: type[TMS],
        call: Callable[P, TMS],
        additional: Callable[[TMS], bool] | None = None,
        handle: Callable[[TMS], TMS | None] | None = None,
    ):
        super().__init__(
            mode=MatchMode.TYPE_CONVERT,
            origin=origin,
            alias=name,
            accepts=MessageSegment,
            validators=[additional] if additional else [],
        )
        self.pattern = name
        self.call = call
        self.handle = handle

    def match(self, input_: MessageSegment) -> TMS:
        if not isinstance(input_, self.origin):
            raise MatchFailed(lang.require("nepattern", "type_error").format(target=type(input_)))
        if input_.type != self.pattern:
            raise MatchFailed(lang.require("nepattern", "content_error").format(target=input_))
        if self.handle:
            if res := self.handle(input_):
                return res
            raise MatchFailed(lang.require("nepattern", "content_error").format(target=input_))
        return input_

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> TMS:
        return self.call(*args, **kwargs)  # type: ignore


class StyleTextPattern(BasePattern[TMS, Union[MessageSegment, str]], Generic[TMS, P]):
    def __init__(
        self,
        name: str,
        origin: type[TMS],
        call: Callable[P, TMS],
        spliter: Callable[[str, list[str]], TMS | None] | None = None,
    ):
        super().__init__(
            mode=MatchMode.TYPE_CONVERT,
            origin=origin,
            alias=name,
            accepts=Union[MessageSegment, str],
        )
        self.pattern = name
        self.call = call
        self.spliter = spliter
        self.expected = [name]

    def match(self, input_: str | MessageSegment) -> TMS:
        if not isinstance(input_, (str, self.origin)):  # type: ignore
            raise MatchFailed(lang.require("nepattern", "type_error").format(target=type(input_)))
        if isinstance(input_, str):
            if self.spliter:
                res = self.spliter(input_, self.expected)
                if not res:
                    raise MatchFailed(lang.require("nepattern", "content_error").format(target=input_))
                return res
            return self.call(input_)  # type: ignore
        if input_.type != self.pattern:
            raise MatchFailed(lang.require("nepattern", "content_error").format(target=input_))
        return input_

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> TMS:
        return self.call(*args, **kwargs)  # type: ignore
    
    def __add__(self, other: StyleTextPattern[TMS, P]) -> Self:
        if not isinstance(other, StyleTextPattern):
            raise TypeError(other)
        if other.pattern not in self.expected:
            self.expected.append(other.pattern)
        return self


MReturn: TypeAlias = Union[
    Union[str, Segment, UniMessage, Message, MessageSegment],
    Awaitable[Union[str, Segment, UniMessage, Message, MessageSegment]],
]
MIDDLEWARE: TypeAlias = Callable[[Event, Bot, T_State, Any], Any]
CHECK: TypeAlias = Callable[[Event, Bot, T_State, Arparma], Awaitable[bool]]
