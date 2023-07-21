from __future__ import annotations

from typing_extensions import ParamSpec, TypeAlias
from typing import Any, Union, Generic, Literal, TypeVar, Callable, Awaitable

from tarina import lang
from nepattern import BasePattern, MatchFailed, PatternModel
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
            PatternModel.TYPE_CONVERT,
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


OutputType = Literal["help", "shortcut", "completion"]
TConvert: TypeAlias = Callable[[OutputType, str], Union[Message, Awaitable[Message]]]
MReturn: TypeAlias = Union[
    Union[str, Message, MessageSegment], Awaitable[Union[str, Message, MessageSegment]]
]


def _isinstance(
    seg: MessageSegment, mapping: dict[str, Callable[[MessageSegment], Any]]
):
    if (key := seg.type) in mapping and (res := mapping[key](seg)):
        return res
    if "*" in mapping and (res := mapping["*"](seg)):
        return res


def gen_unit(
    model: type[T],
    mapping: dict[str, Callable[[MessageSegment], T | Literal[False] | None]],
    additional: Callable[..., bool] | None = None,
) -> BasePattern[T]:
    return BasePattern(
        model.__name__,
        PatternModel.TYPE_CONVERT,
        model,
        lambda self, x: _isinstance(x, mapping),
        accepts=[MessageSegment],
        alias=model.__name__,
        validators=[additional] if additional else [],
    )
