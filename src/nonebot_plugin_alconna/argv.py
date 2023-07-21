from __future__ import annotations

from nonebot.adapters import Message
from arclet.alconna._internal._argv import Argv
from arclet.alconna.argv import argv_config, set_default_argv_type


class MessageArgv(Argv[Message]):
    @staticmethod
    def generate_token(data: list) -> int:
        return hash("".join(i.__repr__() for i in data))


set_default_argv_type(MessageArgv)
argv_config(
    MessageArgv,
    filter_out=[],
    checker=lambda x: isinstance(x, Message),
    to_text=lambda x: x if x.__class__ is str else str(x) if x.is_text() else None,
)
