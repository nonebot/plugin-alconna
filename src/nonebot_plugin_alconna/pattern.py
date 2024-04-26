from typing import Any, List, Type, Union, Literal, Optional, overload

from nepattern import MatchMode, BasePattern, func

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
Custom = BasePattern.of(segment.Custom)


@overload
def select(
    seg: Union[Type[segment.TS], BasePattern[segment.TS, segment.Segment, Any]],
) -> BasePattern[List[segment.TS], segment.Segment, Literal[MatchMode.TYPE_CONVERT]]: ...


@overload
def select(
    seg: Union[Type[segment.TS], BasePattern[segment.TS, segment.Segment, Any]], index: int = 0
) -> BasePattern[segment.TS, segment.Segment, Literal[MatchMode.TYPE_CONVERT]]: ...


def select(
    seg: Union[Type[segment.TS], BasePattern[segment.TS, segment.Segment, Any]], index: Optional[int] = None
) -> Union[
    BasePattern[List[segment.TS], segment.Segment, Literal[MatchMode.TYPE_CONVERT]],
    BasePattern[segment.TS, segment.Segment, Literal[MatchMode.TYPE_CONVERT]],
]:
    if isinstance(seg, BasePattern):
        _type = seg.origin

        def query(segs: List[segment.Segment]):
            for s in segs:
                res = seg.validate(s)
                if res.success:
                    yield res.value()
                yield from query(s.children)

        if index is None:

            def converter(self, _seg: segment.Segment):
                results = []
                _res = seg.validate(_seg)
                if _res.success:
                    results.append(_res.value())
                results.extend(query(_seg.children))
                if not results:
                    return None
                return results

            return BasePattern(
                mode=MatchMode.TYPE_CONVERT,
                origin=List[segment.TS],
                converter=converter,
                accepts=segment.Segment,
                alias=f"select({_type.__name__})",
            )

        def converter1(self, _seg: segment.Segment):
            results = []
            _res = seg.validate(_seg)
            if _res.success:
                results.append(_res.value())
            results.extend(query(_seg.children))
            if not results:
                return None
            return results[index]

        return BasePattern(
            mode=MatchMode.TYPE_CONVERT,
            origin=_type,
            converter=converter1,
            accepts=segment.Segment,
            alias=f"select({_type.__name__})[{index}]",
        )

    else:
        _type = seg

        def query1(segs: List[segment.Segment]):
            for s in segs:
                if isinstance(s, _type):
                    yield s
                yield from query1(s.children)

        if index is None:

            def converter(self, _seg: segment.Segment):
                results = []
                if isinstance(_seg, _type):
                    results.append(_seg)
                results.extend(query1(_seg.children))
                if not results:
                    return None
                return results

            return BasePattern(
                mode=MatchMode.TYPE_CONVERT,
                origin=List[segment.TS],
                converter=converter,
                accepts=segment.Segment,
                alias=f"select({_type.__name__})",
            )

        def converter1(self, _seg: segment.Segment):
            results = []
            if isinstance(_seg, _type):
                results.append(_seg)
            results.extend(query1(_seg.children))
            if not results:
                return None
            return results[index]

        return BasePattern(
            mode=MatchMode.TYPE_CONVERT,
            origin=_type,
            converter=converter1,
            accepts=segment.Segment,
            alias=f"select({_type.__name__})[{index}]",
        )


def select_first(
    seg: Union[Type[segment.TS], BasePattern[segment.TS, segment.Segment, Any]]
) -> BasePattern[segment.TS, segment.Segment, Literal[MatchMode.TYPE_CONVERT]]:
    return select(seg, 0)


def select_last(
    seg: Union[Type[segment.TS], BasePattern[segment.TS, segment.Segment, Any]]
) -> BasePattern[segment.TS, segment.Segment, Literal[MatchMode.TYPE_CONVERT]]:
    return select(seg, -1)


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
    "Custom": segment.Custom,
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
