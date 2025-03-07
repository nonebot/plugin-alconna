from nonebot_plugin_alconna.uniseg.loader import BaseLoader
from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter


class Loader(BaseLoader):
    def get_adapter(self) -> SupportAdapter:
        return SupportAdapter.wxmp

    def get_builder(self):
        from .builder import WXMPMessageBuilder

        return WXMPMessageBuilder()

    def get_exporter(self):
        from .exporter import WXMPMessageExporter

        return WXMPMessageExporter()
