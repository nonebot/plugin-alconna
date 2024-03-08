from nonebot_plugin_alconna.uniseg.loader import BaseLoader
from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter


class Loader(BaseLoader):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.mirai

    @classmethod
    def get_builder(cls):
        from .builder import MiraiMessageBuilder

        return MiraiMessageBuilder()

    @classmethod
    def get_exporter(cls):
        from .exporter import MiraiMessageExporter

        return MiraiMessageExporter()
