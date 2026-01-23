from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.loader import BaseLoader


class Loader(BaseLoader):
    def get_adapter(self) -> SupportAdapter:
        return SupportAdapter.yunhu

    def get_builder(self):
        from .builder import YunHuMessageBuilder

        return YunHuMessageBuilder()

    def get_exporter(self):
        from .exporter import YunHuMessageExporter

        return YunHuMessageExporter()
