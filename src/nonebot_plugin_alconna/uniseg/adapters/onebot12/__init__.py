from nonebot_plugin_alconna.uniseg.loader import BaseLoader
from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter


class Loader(BaseLoader):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.onebot12

    @classmethod
    def get_builder(cls):
        from .builder import Onebot12MessageBuilder

        return Onebot12MessageBuilder()

    @classmethod
    def get_exporter(cls):
        from .exporter import Onebot12MessageExporter

        return Onebot12MessageExporter()
