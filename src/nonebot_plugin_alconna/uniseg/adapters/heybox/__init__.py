from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.loader import BaseLoader


class Loader(BaseLoader):
    def get_adapter(self) -> SupportAdapter:
        return SupportAdapter.heybox

    def get_builder(self):
        from .builder import HeyboxMessageBuilder

        return HeyboxMessageBuilder()

    def get_exporter(self):
        from .exporter import HeyboxMessageExporter

        return HeyboxMessageExporter()
