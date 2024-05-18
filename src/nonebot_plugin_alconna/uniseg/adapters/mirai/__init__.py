from nonebot_plugin_alconna.uniseg.loader import BaseLoader
from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter


class Loader(BaseLoader):
    def get_adapter(self) -> SupportAdapter:
        return SupportAdapter.mirai_official

    def get_builder(self):
        from .builder import MiraiMessageBuilder

        return MiraiMessageBuilder()

    def get_exporter(self):
        from .exporter import MiraiMessageExporter

        return MiraiMessageExporter()

    def get_fetcher(self):
        from .target import MiraiTargetFetcher

        return MiraiTargetFetcher()
