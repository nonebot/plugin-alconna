from __future__ import annotations

from typing_extensions import Self
from typing import TypeVar, Callable, Iterable

from tarina import lang
from arclet.alconna import NullMessage
from nonebot.adapters import Message, MessageSegment
from arclet.alconna.argv import Argv, set_default_argv_type

from .uniseg import Segment, UniMessage, FallbackMessage

TM = TypeVar("TM", Message, UniMessage)


def _default_builder(self: MessageArgv, data: Message | UniMessage):
    for unit in data:
        if not self.is_text(unit):
            self.raw_data.append(unit)
            self.ndata += 1
        elif res := unit.data["text"].strip():
            self.raw_data.append(res)
            self.ndata += 1


class MessageArgv(Argv[TM]):
    is_text: Callable[[MessageSegment | Segment], bool]

    @classmethod
    def custom_build(
        cls,
        target: type[TM],
        is_text: Callable[[MessageSegment | Segment], bool] = lambda x: x.is_text(),
        builder: Callable[[MessageArgv, TM], None] = _default_builder,
        cleanup: Callable[..., None] = lambda: None,
    ):
        cls._cache.setdefault(target, {}).update(
            {
                "is_text": is_text,
                "builder": builder,
                "cleanup": cleanup,
            }
        )

    def __post_init__(self):
        super().__post_init__()
        self.is_text = lambda x: x.is_text()

    @staticmethod
    def generate_token(data: list) -> int:
        return hash("".join(i.__class__.__name__ + i.__repr__() for i in data))

    def build(self, data: TM) -> Self:
        """命令分析功能, 传入字符串或消息链

        Args:
            data (TDC): 命令

        Returns:
            Self: 自身
        """
        self.reset()
        if not isinstance(data, (Message, UniMessage)):
            data = FallbackMessage(data)  # type: ignore
        cache = self.__class__._cache.get(data.__class__, {})
        if "cleanup" in cache:
            cache["cleanup"]()
        self.is_text = cache.get("is_text", self.is_text)
        self.converter = lambda x: data.__class__(x)
        self.origin = data
        cache.get("builder", _default_builder)(self, data)
        if self.ndata < 1:
            raise NullMessage(lang.require("argv", "null_message").format(target=data))
        self.bak_data = self.raw_data.copy()
        if self.message_cache:
            self.token = self.generate_token(self.raw_data)
        return self

    def addon(self, data: Iterable[str | MessageSegment]) -> Self:
        """添加命令元素

        Args:
            data (Iterable[str | MessageSegment]): 命令元素

        Returns:
            Self: 自身
        """
        for i, d in enumerate(data):
            if not d:
                continue
            if d.__class__ is str:
                text = d
            elif self.is_text(d):  # type: ignore
                text = d.data["text"]  # type: ignore
            else:
                self.raw_data.append(d)
                self.ndata += 1
                continue
            if not text.strip("\xa0").strip():  # type: ignore
                continue
            if i > 0 and isinstance(self.raw_data[-1], str):
                self.raw_data[-1] += f"{self.separators[0]}{text}"
            else:
                self.raw_data.append(text)
                self.ndata += 1
        self.bak_data = self.raw_data.copy()
        if self.message_cache:
            self.token = self.generate_token(self.raw_data)
        return self


set_default_argv_type(MessageArgv)
