from dataclasses import dataclass

from nonebot.adapters import Bot
from nonebot.adapters.satori import Message, MessageSegment
from nonebot.adapters import MessageSegment as BaseMessageSegment
from nonebot.adapters.satori.message import Custom as CustomSegment

from nonebot_plugin_alconna.uniseg.builder import MessageBuilder
from nonebot_plugin_alconna.uniseg.exporter import MessageExporter
from nonebot_plugin_alconna.uniseg import Emoji, Segment, custom_handler, custom_register


@dataclass
class MarketFace(Segment):
    tabId: str
    faceId: str
    key: str


@custom_register(MarketFace, "chronocat:marketface")
def mfbuild(builder: MessageBuilder, seg: BaseMessageSegment):
    if not isinstance(seg, CustomSegment):
        raise ValueError("MarketFace can only be built from Satori Message")
    return MarketFace(**seg.data)(*builder.generate(seg.children))


@custom_handler(MarketFace)
async def mfexport(exporter: MessageExporter, seg: MarketFace, bot: Bot, fallback: bool):
    if exporter.get_message_type() is Message:
        return MessageSegment("chronocat:marketface", seg.data)(await exporter.export(seg.children, bot, fallback))  # type: ignore


@custom_register(Emoji, "chronocat:face")
def fbuild(builder: MessageBuilder, seg: BaseMessageSegment):
    if not isinstance(seg, CustomSegment):
        raise ValueError("Emoji can only be built from Satori Message")
    return Emoji(seg.data["id"], seg.data.get("name"))(*builder.generate(seg.children))


@custom_handler(Emoji)
async def fexport(exporter: MessageExporter, seg: Emoji, bot: Bot, fallback: bool):
    if exporter.get_message_type() is Message:
        return MessageSegment("chronocat:face", seg.data)(await exporter.export(seg.children, bot, fallback))  # type: ignore
