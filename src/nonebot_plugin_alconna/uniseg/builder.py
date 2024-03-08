from abc import ABCMeta, abstractmethod
from typing import Any, Dict, List, Union, TypeVar, Callable, Optional

from nonebot.adapters import Bot, Event, Message, MessageSegment

from .constraint import SupportAdapter
from .segment import Text, Other, Reply, Segment, custom

TS = TypeVar("TS", bound=MessageSegment)


def build(*types: str):
    def wrapper(func: Union[Callable[[Any, TS], Optional[Segment]], Callable[[Any, TS], List[Segment]]]):
        if types:
            func.__build_target__ = types
        return func

    return wrapper


class MessageBuilder(metaclass=ABCMeta):
    _mapping: Dict[
        str,
        Union[Callable[[MessageSegment], Optional[Segment]], Callable[[MessageSegment], List[Segment]]],
    ]

    @classmethod
    @abstractmethod
    def get_adapter(cls) -> SupportAdapter: ...

    def __init__(self):
        self._mapping = {}
        for attr in self.__class__.__dict__.values():
            if callable(attr) and hasattr(attr, "__build_target__"):
                method = getattr(self, attr.__name__)
                target = attr.__build_target__
                for _type in target:
                    self._mapping[_type] = method

    def preprocess(self, source: Message[TS]) -> Message[TS]:
        return source

    def convert(self, seg: MessageSegment) -> Union[Segment, List[Segment]]:
        seg_type = seg.type
        if seg_type in self._mapping:
            res = self._mapping[seg_type](seg)
            if not res:
                return custom.solve(seg) or Other(seg)
            if isinstance(res, list):
                for _seg in res:
                    _seg.origin = seg
            else:
                res.origin = seg
            return res
        if seg.is_text():
            if seg.type == "text":
                if "styles" in seg.data:
                    res = Text(seg.data["text"], seg.data["styles"])
                else:
                    res = Text(seg.data["text"])
            else:
                res = Text(seg.data["text"]).mark(0, len(seg.data["text"]), seg.type)
            res.origin = seg
            return res
        return custom.solve(seg) or Other(seg)

    def generate(self, source: Message[MessageSegment]) -> List[Segment]:
        result = []
        for ms in self.preprocess(source):
            seg = self.convert(ms)
            result.extend(seg if isinstance(seg, list) else [seg])
        return result

    async def extract_reply(self, event: Event, bot: Bot) -> Union[Reply, None]:
        return
