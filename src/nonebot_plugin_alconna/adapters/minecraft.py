from arclet.alconna import argv_config, set_default_argv_type
from nonebot.adapters.minecraft.message import Message, BaseMessage, MessageSegment

from nonebot_plugin_alconna.argv import MessageArgv
from nonebot_plugin_alconna.typings import SegmentPattern


class MinecraftMessageArgv(MessageArgv):
    ...


set_default_argv_type(MinecraftMessageArgv)
argv_config(
    MinecraftMessageArgv,
    filter_out=[],
    checker=lambda x: isinstance(x, BaseMessage),
    to_text=lambda x: x if x.__class__ is str else str(x) if x.type == "text" else None,
    converter=lambda x: Message(x),
)

Text = str
Image = SegmentPattern("image", MessageSegment, MessageSegment.image)
Video = SegmentPattern("video", MessageSegment, MessageSegment.video)
