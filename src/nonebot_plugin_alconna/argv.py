from __future__ import annotations

from typing_extensions import Self
from typing import Callable, Iterable

from tarina import lang
from nonebot.adapters import Message
from arclet.alconna import NullMessage
from arclet.alconna.argv import Argv, set_default_argv_type

from .uniseg import Text, Segment, UniMessage, FallbackMessage


def _default_builder(self: MessageArgv, data: UniMessage[Segment]):
    for unit in data:
        if not isinstance(unit, Text):
            self.raw_data.append(unit)
            self.ndata += 1
        elif res := unit.text.strip():
            self.raw_data.append(res)
            self.ndata += 1


class MessageArgv(Argv[UniMessage]):

    @classmethod
    def custom_build(
        cls,
        target: type[Message],
        builder: Callable[[MessageArgv, UniMessage], None] = _default_builder,
        cleanup: Callable[..., None] = lambda: None,
    ):
        cls._cache.setdefault(target, {}).update(
            {
                "builder": builder,
                "cleanup": cleanup,
            }
        )

    @staticmethod
    def generate_token(data: list) -> int:
        return hash("".join(i.__class__.__name__ + i.__repr__() for i in data))

    def build(self, data: UniMessage) -> Self:
        """命令分析功能, 传入字符串或消息链

        Args:
            data (TDC): 命令

        Returns:
            Self: 自身
        """
        self.reset()
        origin_class = self.context.get("message_type", FallbackMessage)
        cache = self.__class__._cache.get(origin_class, {})
        if "cleanup" in cache:
            cache["cleanup"]()
        self.converter = lambda x: UniMessage(x)
        self.origin = data
        cache.get("builder", _default_builder)(self, data)
        if self.ndata < 1:
            raise NullMessage(lang.require("argv", "null_message").format(target=data))
        self.bak_data = self.raw_data.copy()
        if self.message_cache:
            self.token = self.generate_token(self.raw_data)
        return self

    def addon(self, data: Iterable[str | Segment], merge_str: bool = True) -> Self:
        """添加命令元素

        Args:
            data (Iterable[str | Segment]): 命令元素
            merge_str (bool, optional): 是否合并前后字符串

        Returns:
            Self: 自身
        """
        for i, d in enumerate(data):
            if not d:
                continue
            if d.__class__ is str:
                text = d
            elif isinstance(d, Text):  # type: ignore
                text = d.text  # type: ignore
            else:
                self.raw_data.append(d)
                self.ndata += 1
                continue
            if not text.strip("\xa0").strip():  # type: ignore
                continue
            if merge_str and i > 0 and isinstance(self.raw_data[-1], str):
                self.raw_data[-1] += f"{self.separators[0]}{text}"
            else:
                self.raw_data.append(text)
                self.ndata += 1
        self.bak_data = self.raw_data.copy()
        if self.message_cache:
            self.token = self.generate_token(self.raw_data)
        return self


set_default_argv_type(MessageArgv)
