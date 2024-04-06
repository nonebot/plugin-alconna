from nonebot_plugin_alconna.uniseg.loader import BaseLoader
from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter


class Loader(BaseLoader):
    def get_adapter(self) -> SupportAdapter:
        return SupportAdapter.kook

    def get_builder(self):
        from .builder import KookMessageBuilder

        return KookMessageBuilder()

    def get_exporter(self):
        from .exporter import KookMessageExporter

        return KookMessageExporter()

    def get_fetcher(self):
        from .target import KookTargetFetcher

        return KookTargetFetcher()
