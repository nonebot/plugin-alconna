from nonebot_plugin_alconna.uniseg.loader import BaseLoader
from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter


class Loader(BaseLoader):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.feishu

    @classmethod
    def get_builder(cls):
        from .builder import FeishuMessageBuilder

        return FeishuMessageBuilder()

    @classmethod
    def get_exporter(cls):
        from .exporter import FeishuMessageExporter

        return FeishuMessageExporter()
