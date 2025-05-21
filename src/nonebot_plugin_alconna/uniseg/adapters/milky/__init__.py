from nonebot_plugin_alconna.uniseg.loader import BaseLoader
from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter


class Loader(BaseLoader):
    def get_adapter(self) -> SupportAdapter:
        return SupportAdapter.milky

    def get_builder(self):
        from .builder import MilkyMessageBuilder

        return MilkyMessageBuilder()

    def get_exporter(self):
        from .exporter import MilkyMessageExporter

        return MilkyMessageExporter()

    def get_fetcher(self):
        from .target import MilkyTargetFetcher

        return MilkyTargetFetcher()
