from nonebot_plugin_alconna.uniseg.loader import BaseLoader
from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter


class Loader(BaseLoader):
    def get_adapter(self) -> SupportAdapter:
        return SupportAdapter.onebot11

    def get_builder(self):
        from .builder import Onebot11MessageBuilder

        return Onebot11MessageBuilder()

    def get_exporter(self):
        from .exporter import Onebot11MessageExporter

        return Onebot11MessageExporter()

    def get_fetcher(self):
        from .target import Onebot11TargetFetcher

        return Onebot11TargetFetcher()
