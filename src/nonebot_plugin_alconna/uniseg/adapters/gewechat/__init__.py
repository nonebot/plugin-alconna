from warnings import warn

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

        warn("Adapter `Gewechat` is deprecated and will be removed in the future.", DeprecationWarning, stacklevel=2)
        return GeWeChatMessageExporter()

    def get_fetcher(self):
        from .target import GeWeChatTargetFetcher

        return GeWeChatTargetFetcher()
