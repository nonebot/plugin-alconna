from nonebot_plugin_alconna.uniseg.loader import BaseLoader
from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter


class Loader(BaseLoader):
    def get_adapter(self) -> SupportAdapter:
        return SupportAdapter.nonebug

    def get_builder(self):
        from .builder import NonebugMessageBuilder

        return NonebugMessageBuilder()

    def get_exporter(self):
        from .exporter import NonebugMessageExporter

        return NonebugMessageExporter()
