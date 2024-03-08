from nonebot_plugin_alconna.uniseg.loader import BaseLoader
from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter


class Loader(BaseLoader):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.onebot11

    @classmethod
    def get_builder(cls):
        from .builder import Onebot11MessageBuilder

        return Onebot11MessageBuilder()

    @classmethod
    def get_exporter(cls):
        from .exporter import Onebot11MessageExporter

        return Onebot11MessageExporter()
