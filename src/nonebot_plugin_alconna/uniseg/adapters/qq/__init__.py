from nonebot_plugin_alconna.uniseg.loader import BaseLoader
from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter


class Loader(BaseLoader):
    def get_adapter(self) -> SupportAdapter:
        return SupportAdapter.qq

    def get_builder(self):
        from .builder import QQMessageBuilder

        return QQMessageBuilder()

    def get_exporter(self):
        from .exporter import QQMessageExporter

        return QQMessageExporter()

    def get_fetcher(self):
        from .target import QQTargetFetcher

        return QQTargetFetcher()
