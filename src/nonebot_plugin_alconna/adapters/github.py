from arclet.alconna import argv_config, set_default_argv_type
from nonebot.adapters.github.message import Message, BaseMessage

from nonebot_plugin_alconna.argv import MessageArgv


class GHMessageArgv(MessageArgv):
    ...


set_default_argv_type(GHMessageArgv)
argv_config(
    GHMessageArgv,
    filter_out=[],
    checker=lambda x: isinstance(x, BaseMessage),
    to_text=lambda x: x if x.__class__ is str else str(x) if x.is_text() else None,
    converter=lambda x: Message(x),
)

Markdown = str
