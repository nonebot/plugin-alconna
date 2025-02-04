from typing_extensions import deprecated
from typing import Any, Union, Generic, Literal, TypeVar, Callable, Optional

from tarina import lang
from arclet.alconna import StrMulti
from nepattern import MatchMode, BasePattern, MatchFailed, func

from .uniseg import segment
from .uniseg.segment import Segment

Image = BasePattern.of(segment.Image)
Text = BasePattern.of(segment.Text)
At = BasePattern.of(segment.At)
AtAll = BasePattern.of(segment.AtAll)
Audio = BasePattern.of(segment.Audio)
Emoji = BasePattern.of(segment.Emoji)
Hyper = BasePattern.of(segment.Hyper)
Video = BasePattern.of(segment.Video)
Voice = BasePattern.of(segment.Voice)
Other = BasePattern.of(segment.Other)
Reply = BasePattern.of(segment.Reply)
File = BasePattern.of(segment.File)
Reference = BasePattern.of(segment.Reference)


TS = TypeVar("TS", bound=Segment)
TS1 = TypeVar("TS1", bound=Segment)
TS2 = TypeVar("TS2", bound=Segment)


class SelectPattern(BasePattern[list[TS], TS2, Literal[MatchMode.TYPE_CONVERT]], Generic[TS, TS2]):
    def __init__(
        self,
        target: type[TS],
        converter: Callable[[Any, TS2], Optional[list[TS]]],
    ):
        super().__init__(
            mode=MatchMode.TYPE_CONVERT,
            origin=list[target],
            converter=converter,
            alias=f"select({target.__name__})",
        )
        self.accept = lambda x: isinstance(x, Segment)

    def match(self, input_: TS2):
        if not self.accept(input_):
            raise MatchFailed(
                lang.require("nepattern", "type_error").format(
                    type=input_.__class__, target=input_, expected=self.alias
                )
            )
        if (res := self.converter(self, input_)) is None:
            raise MatchFailed(lang.require("nepattern", "content_error").format(target=input_, expected=self.alias))
        return res  # type: ignore

    def nth(self, index: int):
        return func.Index(self, index)

    @property
    def first(self):
        return func.Index(self, 0)

    @property
    def last(self):
        return func.Index(self, -1)

    def from_(self, seg: Union[type[TS1], BasePattern[TS1, Segment, Any]]) -> "SelectPattern[TS, TS1]":
        _self = self.copy()
        if isinstance(seg, BasePattern):
            _self.accept = lambda x: seg.validate(x).flag == "valid"  # type: ignore
        else:
            _self.accept = lambda x: isinstance(x, seg)  # type: ignore
        _self.alias = f"{self.alias}.from({seg if isinstance(seg, BasePattern) else seg.__name__})"
        _self.refresh()
        return _self  # type: ignore


def select(
    seg: Union[type[TS], BasePattern[TS, Segment, Any]],
) -> SelectPattern[TS, Segment]:
    if isinstance(seg, BasePattern):
        _type = seg.origin

        def query(segs: list[Segment]):
            for s in segs:
                res = seg.validate(s)
                if res.success:
                    yield res.value()
                yield from query(s.children)

        def converter(self, _seg: Segment):
            results = []
            _res = seg.validate(_seg)
            if _res.success:
                results.append(_res.value())
            results.extend(query(_seg.children))
            if not results:
                return None
            return results

    else:
        _type: type[TS] = seg

        def query1(segs: list[Segment]):
            for s in segs:
                if isinstance(s, _type):
                    yield s
                yield from query1(s.children)

        def converter(self, _seg: Segment):
            results = []
            if isinstance(_seg, _type):
                results.append(_seg)
            results.extend(query1(_seg.children))
            if not results:
                return None
            return results

    return SelectPattern(
        target=_type,
        converter=converter,
    )


@deprecated("Use `select().first` instead.")
def select_first(
    seg: Union[type[segment.TS], BasePattern[segment.TS, Segment, Any]],
) -> BasePattern[segment.TS, Segment, Literal[MatchMode.TYPE_CONVERT]]:
    return select(seg).first


@deprecated("Use `select().last` instead.")
def select_last(
    seg: Union[type[segment.TS], BasePattern[segment.TS, Segment, Any]],
) -> BasePattern[segment.TS, Segment, Literal[MatchMode.TYPE_CONVERT]]:
    return select(seg).last


patterns = {
    "text": StrMulti,
    "Image": segment.Image,
    "Text": segment.Text,
    "At": segment.At,
    "AtAll": segment.AtAll,
    "Audio": segment.Audio,
    "Emoji": segment.Emoji,
    "Hyper": segment.Hyper,
    "Video": segment.Video,
    "Voice": segment.Voice,
    "Other": segment.Other,
    "Reply": segment.Reply,
    "File": segment.File,
    "Reference": segment.Reference,
    "select": select,
    "Dot": func.Dot,
    "Filter": func.Filter,
    "GetItem": func.GetItem,
    "Index": func.Index,
    "Join": func.Join,
    "Lower": func.Lower,
    "Map": func.Map,
    "Reduce": func.Reduce,
    "Slice": func.Slice,
    "Step": func.Step,
    "Sum": func.Sum,
    "Upper": func.Upper,
}
