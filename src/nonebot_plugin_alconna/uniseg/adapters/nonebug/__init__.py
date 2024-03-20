from nonebot_plugin_alconna.uniseg.loader import BaseLoader
from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter


class Loader(BaseLoader):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.nonebug

    @classmethod
    def get_builder(cls):
        from .builder import NonebugMessageBuilder

        return NonebugMessageBuilder()

    @classmethod
    def get_exporter(cls):
        from .exporter import NonebugMessageExporter

        return NonebugMessageExporter()
