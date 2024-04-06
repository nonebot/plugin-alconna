from nonebot_plugin_alconna.uniseg.loader import BaseLoader
from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter


class Loader(BaseLoader):
    def get_adapter(self) -> SupportAdapter:
        return SupportAdapter.satori

    def get_builder(self):
        from .builder import SatoriMessageBuilder

        return SatoriMessageBuilder()

    def get_exporter(self):
        from .exporter import SatoriMessageExporter

        return SatoriMessageExporter()

    def get_fetcher(self):
        from .target import SatoriTargetFetcher

        return SatoriTargetFetcher()
