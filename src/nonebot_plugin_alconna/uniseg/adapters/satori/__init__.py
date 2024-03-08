from nonebot_plugin_alconna.uniseg.loader import BaseLoader
from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter


class Loader(BaseLoader):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.satori

    @classmethod
    def get_builder(cls):
        from .builder import SatoriMessageBuilder

        return SatoriMessageBuilder()

    @classmethod
    def get_exporter(cls):
        from .exporter import SatoriMessageExporter

        return SatoriMessageExporter()
