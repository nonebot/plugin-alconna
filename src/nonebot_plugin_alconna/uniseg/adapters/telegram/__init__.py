from nonebot_plugin_alconna.uniseg.loader import BaseLoader
from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter


class Loader(BaseLoader):
    def get_adapter(self) -> SupportAdapter:
        return SupportAdapter.telegram

    def get_builder(self):
        from .builder import TelegramMessageBuilder

        return TelegramMessageBuilder()

    def get_exporter(self):
        from .exporter import TelegramMessageExporter

        return TelegramMessageExporter()
