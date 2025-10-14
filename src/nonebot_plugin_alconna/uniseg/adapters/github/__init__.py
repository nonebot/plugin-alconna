from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.loader import BaseLoader


class Loader(BaseLoader):
    def get_adapter(self) -> SupportAdapter:
        return SupportAdapter.github

    def get_builder(self):
        from .builder import GithubMessageBuilder

        return GithubMessageBuilder()

    def get_exporter(self):
        from .exporter import GithubMessageExporter

        return GithubMessageExporter()
