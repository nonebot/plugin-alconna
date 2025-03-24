from nonebot_plugin_alconna.uniseg.loader import BaseLoader
from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter


class Loader(BaseLoader):
    def get_adapter(self) -> SupportAdapter:
        return SupportAdapter.gewechat

    def get_builder(self):
        from .builder import GeWeChatMessageBuilder

        return GeWeChatMessageBuilder()

    def get_exporter(self):
        from .exporter import GeWeChatMessageExporter

        return GeWeChatMessageExporter()

    def get_fetcher(self):
        from .target import GeWeChatTargetFetcher

        return GeWeChatTargetFetcher()
