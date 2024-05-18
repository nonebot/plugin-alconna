from nonebot_plugin_alconna.uniseg.loader import BaseLoader
from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter


class Loader(BaseLoader):
    def get_adapter(self) -> SupportAdapter:
        return SupportAdapter.mirai_community

    def get_builder(self):
        from .builder import Mirai2MessageBuilder

        return Mirai2MessageBuilder()

    def get_exporter(self):
        from .exporter import Mirai2MessageExporter

        return Mirai2MessageExporter()

    def get_fetcher(self):
        from .target import Mirai2TargetFetcher

        return Mirai2TargetFetcher()
