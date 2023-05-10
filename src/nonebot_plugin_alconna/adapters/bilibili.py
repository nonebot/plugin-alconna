from nonebot.adapters.billibili.message import Message, BaseMessage
from nonebot_plugin_alconna.argv import MessageArgv
from arclet.alconna import set_default_argv_type, argv_config


class BiliMessageArgv(MessageArgv):
    ...


set_default_argv_type(BiliMessageArgv)
argv_config(
    BiliMessageArgv,
    filter_out=[],
    checker=lambda x: isinstance(x, BaseMessage),
    to_text=lambda x: x if x.__class__ is str else str(x) if x.is_text() else None,
    converter=lambda x: Message(x)
)
Danmu = str
