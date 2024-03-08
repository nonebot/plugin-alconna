from nonebot_plugin_alconna.uniseg.loader import BaseLoader
from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter


class Loader(BaseLoader):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.telegram

    @classmethod
    def get_builder(cls):
        from .builder import TelegramMessageBuilder

        return TelegramMessageBuilder()

    @classmethod
    def get_exporter(cls):
        from .exporter import TelegramMessageExporter

        return TelegramMessageExporter()
