from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.loader import BaseLoader


class Loader(BaseLoader):
    def get_adapter(self) -> SupportAdapter:
        return SupportAdapter.ntchat

    def get_builder(self):
        from .builder import NTChatMessageBuilder

        return NTChatMessageBuilder()

    def get_exporter(self):
        from .exporter import NTChatMessageExporter

        return NTChatMessageExporter()
