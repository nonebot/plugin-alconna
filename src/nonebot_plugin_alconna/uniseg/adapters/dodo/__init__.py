from nonebot_plugin_alconna.uniseg.loader import BaseLoader
from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter


class Loader(BaseLoader):
    def get_adapter(self) -> SupportAdapter:
        return SupportAdapter.dodo

    def get_builder(self):
        from .builder import DodoMessageBuilder

        return DodoMessageBuilder()

    def get_exporter(self):
        from .exporter import DoDoMessageExporter

        return DoDoMessageExporter()

    def get_fetcher(self):
        from .target import DodoTargetFetcher

        return DodoTargetFetcher()
