from __future__ import annotations

from typing import Callable, Any, TypeVar, Generic, Literal, Awaitable, Union
from typing_extensions import ParamSpec, TypeAlias
from tarina import lang
from nepattern import BasePattern, PatternModel, MatchFailed
from nonebot.internal.adapter.message import MessageSegment, Message

TMS = TypeVar("TMS", bound=MessageSegment)
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


def _isinstance(seg: MessageSegment, accepts: set[str]):
    return seg if seg.type.lower() in accepts else None


def gen_unit(
    name: str, accepts: set[str], additional: Callable[..., bool] | None = None
) -> BasePattern[MessageSegment]:
    return BasePattern(
        name,
        PatternModel.TYPE_CONVERT,
        Any,
        lambda self, x: _isinstance(x, accepts),
        accepts=[MessageSegment],
        validators=[additional] if additional else [],
    )
