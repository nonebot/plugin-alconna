from nonebot_plugin_alconna.uniseg.loader import BaseLoader
from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter


class Loader(BaseLoader):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.ding

    @classmethod
    def get_builder(cls):
        from .builder import DingMessageBuilder

        return DingMessageBuilder()

    @classmethod
    def get_exporter(cls):
        from .exporter import DingMessageExporter

        return DingMessageExporter()
