from __future__ import annotations

from typing import Callable, Any, TypeVar, Generic
from typing_extensions import ParamSpec
from tarina import lang
from nepattern import BasePattern, PatternModel, MatchFailed
from nonebot.internal.adapter.message import MessageSegment

TMS = TypeVar("TMS", bound=MessageSegment)
P = ParamSpec("P")


def _isinstance(self: BasePattern, seg: MessageSegment):
    return seg if self.pattern == seg.type else None


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
