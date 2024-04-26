from typing import List, Type, Union, Literal, Optional, overload

from nepattern import MatchMode, BasePattern

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
    seg: Type[segment.TS],
) -> BasePattern[List[segment.TS], segment.Segment, Literal[MatchMode.TYPE_CONVERT]]: ...


@overload
def select(
    seg: Type[segment.TS], index: int = 0
) -> BasePattern[segment.TS, segment.Segment, Literal[MatchMode.TYPE_CONVERT]]: ...


def select(seg: Type[segment.TS], index: Optional[int] = None) -> Union[
    BasePattern[List[segment.TS], segment.Segment, Literal[MatchMode.TYPE_CONVERT]],
    BasePattern[segment.TS, segment.Segment, Literal[MatchMode.TYPE_CONVERT]],
]:
    def query(segs: List[segment.Segment]):
        for s in segs:
            if isinstance(s, seg):
                yield s
            yield from query(s.children)

    if index is None:

        def converter(self, _seg: segment.Segment):
            results = []
            if isinstance(_seg, seg):
                results.append(_seg)
            results.extend(query(_seg.children))
            if not results:
                return None
            return results

        return BasePattern(
            mode=MatchMode.TYPE_CONVERT,
            origin=List[segment.TS],
            converter=converter,
            accepts=segment.Segment,
            alias=f"select({seg.__name__})",
        )

    def converter1(self, _seg: segment.Segment):
        results = []
        if isinstance(_seg, seg):
            results.append(_seg)
        results.extend(query(_seg.children))
        if not results:
            return None
        return results[index]

    return BasePattern(
        mode=MatchMode.TYPE_CONVERT,
        origin=seg,
        converter=converter1,
        accepts=segment.Segment,
        alias=f"select({seg.__name__})[{index}]",
    )


def select_first(seg: Type[segment.TS]) -> BasePattern[segment.TS, segment.Segment, Literal[MatchMode.TYPE_CONVERT]]:
    return select(seg, 0)


def select_last(seg: Type[segment.TS]) -> BasePattern[segment.TS, segment.Segment, Literal[MatchMode.TYPE_CONVERT]]:
    return select(seg, -1)
