from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.loader import BaseLoader


class Loader(BaseLoader):
    def get_adapter(self) -> SupportAdapter:
        return SupportAdapter.discord

    def get_builder(self):
        from .builder import DiscordMessageBuilder

        return DiscordMessageBuilder()

    def get_exporter(self):
        from .exporter import DiscordMessageExporter

        return DiscordMessageExporter()

    def get_fetcher(self):
        from .target import DiscordTargetFetcher

        return DiscordTargetFetcher()
