from __future__ import annotations

from nonebot.adapters import Message, MessageSegment
from arclet.alconna.argv import Argv, argv_config, set_default_argv_type


class FallbackSegment(MessageSegment["FallbackMessage"]):

    @classmethod
    def get_message_class(cls):
        return FallbackMessage

    def __str__(self) -> str:
        if self.type == "text":
            return self.data["text"]
        return f"[{self.type}][{self.data}]"

    def is_text(self) -> bool:
        return self.type == "text"

    @staticmethod
    def text(text: str) -> FallbackSegment:
        return FallbackSegment("text", {"text": text})


class FallbackMessage(Message[FallbackSegment]):

    @classmethod
    def get_segment_class(cls):
        return FallbackSegment

    @staticmethod
    def _construct(msg: str):
        yield FallbackSegment.text(msg)


class MessageArgv(Argv[Message]):
    @staticmethod
    def generate_token(data: list) -> int:
        return hash("".join(i.__class__.__name__ + i.__repr__() for i in data))


set_default_argv_type(MessageArgv)
argv_config(
    MessageArgv,
    filter_out=[],
    checker=lambda x: isinstance(x, Message),
    to_text=lambda x: x if x.__class__ is str else str(x) if x.is_text() else None,
    converter=lambda x: FallbackMessage(x),
)
