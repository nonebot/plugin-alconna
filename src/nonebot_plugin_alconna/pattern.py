from typing_extensions import deprecated
from typing import Any, Union, Generic, Literal, TypeVar, Callable, Optional

from tarina import lang
from nepattern import MatchMode, BasePattern, MatchFailed, func

from .uniseg import segment

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


TS = TypeVar("TS", bound=segment.Segment)
TS1 = TypeVar("TS1", bound=segment.Segment)
TS2 = TypeVar("TS2", bound=segment.Segment)


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
        self._accepts = (segment.Segment,)

    def match(self, input_: TS2):
        if not isinstance(input_, self._accepts):
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

    def from_(self, seg: Union[type[TS1], BasePattern[TS1, segment.Segment, Any]]) -> "SelectPattern[TS, TS1]":
        _self = self.copy()
        if isinstance(seg, BasePattern):
            _type = seg.origin
        else:
            _type = seg
        _self._accepts = (_type,)
        return _self  # type: ignore


def select(
    seg: Union[type[TS], BasePattern[TS, segment.Segment, Any]],
) -> SelectPattern[TS, segment.Segment]:
    if isinstance(seg, BasePattern):
        _type = seg.origin

        def query(segs: list[segment.Segment]):
            for s in segs:
                res = seg.validate(s)
                if res.success:
                    yield res.value()
                yield from query(s.children)

        def converter(self, _seg: segment.Segment):
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

        def query1(segs: list[segment.Segment]):
            for s in segs:
                if isinstance(s, _type):
                    yield s
                yield from query1(s.children)

        def converter(self, _seg: segment.Segment):
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
    seg: Union[type[segment.TS], BasePattern[segment.TS, segment.Segment, Any]]
) -> BasePattern[segment.TS, segment.Segment, Literal[MatchMode.TYPE_CONVERT]]:
    return select(seg).first


@deprecated("Use `select().last` instead.")
def select_last(
    seg: Union[type[segment.TS], BasePattern[segment.TS, segment.Segment, Any]]
) -> BasePattern[segment.TS, segment.Segment, Literal[MatchMode.TYPE_CONVERT]]:
    return select(seg).last


patterns = {
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
    "select_first": select_first,
    "select_last": select_last,
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
