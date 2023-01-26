from __future__ import annotations

from typing import Any
from typing_extensions import Self

from arclet.alconna.exceptions import NullMessage
from arclet.alconna.config import config
from arclet.alconna.analysis.analyser import Analyser
from arclet.alconna.analysis.container import DataCollectionContainer

from nonebot.adapters import Message


class MessageContainer(DataCollectionContainer):
    @staticmethod
    def generate_token(data: list[Any | list[str]]) -> int:
        return hash(''.join(i.__repr__() for i in data))

    def build(self, data: Message) -> Self:
        if not isinstance(data, Message):
            exp = ValueError(f"{data} is not a Message")
            raise exp
        self.reset()
        self.temporary_data["origin"] = data
        i, exc = 0, None
        for unit in data:
            if (uname := unit.__class__.__name__) in self.filter_out:
                continue
            if (proc := self.preprocessors.get(uname)) and (res := proc(unit)):
                unit = res
            if isinstance(unit, str):
                if not (res := unit.strip()):
                    continue
                self.raw_data.append(res)
            else:
                self.raw_data.append(unit)
            i += 1
        if i < 1:
            raise NullMessage(config.lang.analyser_handle_null_message.format(target=data))
        self.ndata = i
        self.bak_data = self.raw_data.copy()
        if self.message_cache:
            self.temp_token = self.generate_token(self.raw_data)
        return self


class NonebotCommandAnalyser(Analyser[MessageContainer, Message]):
    """Nonebot 相关的解析器"""

    @staticmethod
    def converter(command: str):
        return Message(command)


NonebotCommandAnalyser.default_container(MessageContainer)
