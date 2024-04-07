from nonebot_plugin_alconna.uniseg.loader import BaseLoader
from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter


class Loader(BaseLoader):
    def get_adapter(self) -> SupportAdapter:
        return SupportAdapter.onebot12

    def get_builder(self):
        from .builder import Onebot12MessageBuilder

        return Onebot12MessageBuilder()

    def get_exporter(self):
        from .exporter import Onebot12MessageExporter

        return Onebot12MessageExporter()

    def get_fetcher(self):
        from .target import Onebot12TargetFetcher

        return Onebot12TargetFetcher()
