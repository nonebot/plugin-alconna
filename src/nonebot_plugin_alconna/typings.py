from __future__ import annotations

from typing_extensions import ParamSpec, TypeAlias
from typing import Any, Union, Generic, Literal, TypeVar, Callable, Awaitable

from tarina import lang
from nepattern import MatchMode, BasePattern, MatchFailed
from nonebot.internal.adapter.message import Message, MessageSegment

T = TypeVar("T")
TMS = TypeVar("TMS", bound=MessageSegment)
TCallable = TypeVar("TCallable", bound=Callable[..., Any])
P = ParamSpec("P")


class SegmentPattern(BasePattern[TMS], Generic[TMS, P]):
    def __init__(
        self,
        name: str,
        origin: type[TMS],
        call: Callable[P, TMS],
        additional: Callable[..., bool] | None = None,
    ):
        super().__init__(
            name,
            MatchMode.TYPE_CONVERT,
            origin,
            alias=name,
            accepts=[MessageSegment],
            validators=[additional] if additional else [],
        )
        self.call = call

    def match(self, input_: str | Any) -> TMS:
        if not isinstance(input_, self.origin):
            raise MatchFailed(
                lang.require("nepattern", "type_error").format(target=type(input_))
            )
        if input_.type != self.pattern:
            raise MatchFailed(
                lang.require("nepattern", "content_error").format(target=input_)
            )
        return input_

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> TMS:
        return self.call(*args, **kwargs)  # type: ignore


class TextSegmentPattern(BasePattern[TMS], Generic[TMS, P]):
    def __init__(
        self,
        name: str,
        origin: type[TMS],
        call: Callable[P, TMS],
        locator: Callable[[str, str], bool] | None = None,
    ):
        super().__init__(
            name,
            MatchMode.TYPE_CONVERT,
            origin,
            alias=name,
            accepts=[MessageSegment, str],
        )
        self.call = call
        self.locator = locator

    def match(self, input_: str | Any) -> TMS:
        if not isinstance(input_, (str, self.origin)):  # type: ignore
            raise MatchFailed(
                lang.require("nepattern", "type_error").format(target=type(input_))
            )
        if isinstance(input_, str):
            if self.locator and not self.locator(input_, self.pattern):
                raise MatchFailed(
                    lang.require("nepattern", "content_error").format(target=input_)
                )
            return self.call(input_)  # type: ignore
        if input_.type != self.pattern:
            raise MatchFailed(
                lang.require("nepattern", "content_error").format(target=input_)
            )
        return input_

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> TMS:
        return self.call(*args, **kwargs)  # type: ignore


OutputType = Literal["help", "shortcut", "completion"]
TConvert: TypeAlias = Callable[[OutputType, str], Union[Message, Awaitable[Message]]]
MReturn: TypeAlias = Union[
    Union[str, Message, MessageSegment], Awaitable[Union[str, Message, MessageSegment]]
]


class UniPattern(BasePattern[T], Generic[T]):
    additional: Callable[..., bool] | None = None

    def __init__(self):
        origin: type[T] = self.__class__.__orig_bases__[0].__args__[0]  # type: ignore
        super().__init__(
            origin.__name__,
            MatchMode.TYPE_CONVERT,
            origin,
            converter=lambda s, x: self.solve(x),
            alias=origin.__name__,
            accepts=[MessageSegment],
            validators=[self.additional] if self.additional else [],
        )

    def solve(self, seg: MessageSegment) -> T | None:
        raise NotImplementedError
