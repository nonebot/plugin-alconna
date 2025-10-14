from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.loader import BaseLoader


class Loader(BaseLoader):
    def get_adapter(self) -> SupportAdapter:
        return SupportAdapter.red

    def get_builder(self):
        from .builder import RedMessageBuilder

        return RedMessageBuilder()

    def get_exporter(self):
        from .exporter import RedMessageExporter

        return RedMessageExporter()

    def get_fetcher(self):
        from .target import RedTargetFetcher

        return RedTargetFetcher()
