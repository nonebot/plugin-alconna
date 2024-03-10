from __future__ import annotations

from contextvars import ContextVar
from typing_extensions import Self
from typing import TYPE_CHECKING, Any, Iterable

from tarina import lang
from nonebot.adapters import Message
from arclet.alconna import NullMessage
from arclet.alconna.argv import Argv, set_default_argv_type

from .uniseg import Text, Segment, UniMessage

argv_ctx: ContextVar[MessageArgv] = ContextVar("argv_ctx")


def _default_builder(self: MessageArgv, data: UniMessage[Segment]):
    for unit in data:
        if not isinstance(unit, Text):
            self.raw_data.append(unit)
            self.ndata += 1
        elif res := unit.text.strip():
            self.raw_data.append(res)
            self.ndata += 1


class MessageArgv(Argv[UniMessage]):

    @staticmethod
    def generate_token(data: list) -> int:
        return hash("".join(i.__class__.__name__ + i.__repr__() for i in data))

    def enter(self, ctx: dict[str, Any] | None = None) -> Self:
        super().enter(ctx)
        self.context["__token__"] = argv_ctx.set(self)
        return self

    def exit(self) -> dict[str, Any]:
        argv_ctx.reset(self.context["__token__"])
        del self.context["__token__"]
        return super().exit()

    def build(self, data: str | list[str] | Message | UniMessage) -> Self:
        """命令分析功能, 传入字符串或消息链

        Args:
            data (TDC): 命令

        Returns:
            Self: 自身
        """
        self.reset()
        if isinstance(data, Message):
            data = UniMessage.generate_without_reply(message=data, adapter=self.context.get("$adapter.name"))
        else:
            data = UniMessage(data)
        self.converter = lambda x: UniMessage(x)
        self.origin = data
        styles = self.context.setdefault("__styles__", {"record": {}, "index": 0, "msg": ""})
        styles["msg"] = data.extract_plain_text()
        _index = 0
        for index, unit in enumerate(data):
            if not isinstance(unit, Text):
                self.raw_data.append(unit)
                self.ndata += 1
                continue
            if not unit.text.strip():
                if not index or index == len(data) - 1:
                    continue
                if not isinstance(data[index - 1], Text) or not isinstance(data[index + 1], Text):
                    continue
            if TYPE_CHECKING:
                assert isinstance(unit, Text)
            text = unit.text
            if not (_styles := unit.styles):
                self.raw_data.append(text)
                self.ndata += 1
                continue
            if self.raw_data and self.raw_data[-1].__class__ is str:
                self.raw_data[-1] = f"{self.raw_data[-1]}{text}"
            else:
                self.raw_data.append(text)
                self.ndata += 1

            start = styles["msg"].find(text, _index)
            for scale, style in _styles.items():
                styles["record"][(start + scale[0], start + scale[1])] = style
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
