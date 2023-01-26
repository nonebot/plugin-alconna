from __future__ import annotations

from nepattern import BasePattern, PatternModel
from nonebot.internal.adapter.message import MessageSegment
from typing import Callable


def _isinstance(self: BasePattern, seg: MessageSegment):
    return seg if self.pattern == seg.type else None


def gen_unit(type_: str, additional: Callable[..., bool] | None = None) -> BasePattern[MessageSegment]:
    return BasePattern(
        type_,
        PatternModel.TYPE_CONVERT,
        MessageSegment,
        _isinstance,
        type_,
        accepts=[MessageSegment],
        validators=[additional] if additional else []
    )
