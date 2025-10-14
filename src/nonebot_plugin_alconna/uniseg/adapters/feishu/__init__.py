from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.loader import BaseLoader


class Loader(BaseLoader):
    def get_adapter(self) -> SupportAdapter:
        return SupportAdapter.feishu

    def get_builder(self):
        from .builder import FeishuMessageBuilder

        return FeishuMessageBuilder()

    def get_exporter(self):
        from .exporter import FeishuMessageExporter

        return FeishuMessageExporter()

    def get_fetcher(self):
        from .target import FeishuTargetFetcher

        return FeishuTargetFetcher()
