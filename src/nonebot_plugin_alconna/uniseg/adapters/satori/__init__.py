from importlib_metadata import PackageNotFoundError, distribution
from nonebot.adapters import MessageSegment as BaseMessageSegment

from nonebot_plugin_alconna.uniseg.loader import BaseLoader
from nonebot_plugin_alconna.uniseg.builder import MessageBuilder
from nonebot_plugin_alconna.uniseg.exporter import MessageExporter
from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.segment import Emoji, custom_handler, custom_register


def get_satori_version():
    try:
        satori = distribution("nonebot-adapter-satori")
    except PackageNotFoundError:
        return None
    else:
        return satori.version


class Loader(BaseLoader):
    def __init__(self):
        if (version := get_satori_version()) and tuple(map(int, version.split(".")[:2])) < (0, 12):
            raise ImportError("nonebot-adapter-satori>=0.12 is required.")

    def get_adapter(self) -> SupportAdapter:
        return SupportAdapter.satori

    def get_builder(self):
        from nonebot.adapters.satori.message import Custom

        from .builder import SatoriMessageBuilder

        @custom_register(Emoji, "chronocat:face")
        def fbuild(builder: MessageBuilder, seg: BaseMessageSegment):
            if not isinstance(seg, Custom):
                raise ValueError("Emoji can only be built from Satori Message")
            return Emoji(seg.data["id"], seg.data.get("name"))(*builder.generate(seg.children))

        return SatoriMessageBuilder()

    def get_exporter(self):
        from nonebot.adapters.satori import Message, MessageSegment

        from .exporter import SatoriMessageExporter

        @custom_handler(Emoji)
        async def fexport(exporter: MessageExporter, seg: Emoji, bot, fallback):
            if exporter.get_message_type() is Message:
                return MessageSegment("chronocat:face", seg.data)(
                    await exporter.export(seg.children, bot, fallback)  # type: ignore
                )
            return None

        return SatoriMessageExporter()

    def get_fetcher(self):
        from .target import SatoriTargetFetcher

        return SatoriTargetFetcher()
