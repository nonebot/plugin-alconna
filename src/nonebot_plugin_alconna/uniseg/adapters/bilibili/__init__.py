from nonebot_plugin_alconna.uniseg.loader import BaseLoader
from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter


class Loader(BaseLoader):
    def get_adapter(self) -> SupportAdapter:
        return SupportAdapter.bilibili

    def get_builder(self):
        from .builder import BilibiliMessageBuilder

        return BilibiliMessageBuilder()

    def get_exporter(self):
        from .exporter import BilibiliMessageExporter

        return BilibiliMessageExporter()
