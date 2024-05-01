from importlib_metadata import PackageNotFoundError, distribution

from nonebot_plugin_alconna.uniseg.loader import BaseLoader
from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter


def get_satori_version():
    try:
        satori = distribution("nonebot-adapter-satori")
        return satori.version
    except PackageNotFoundError:
        return None


class Loader(BaseLoader):

    def __init__(self):
        if version := get_satori_version():
            if tuple(map(int, version.split(".")[:2])) < (0, 11):
                raise ImportError("nonebot-adapter-satori>=0.11 is required.")

    def get_adapter(self) -> SupportAdapter:
        return SupportAdapter.satori

    def get_builder(self):
        from .builder import SatoriMessageBuilder

        return SatoriMessageBuilder()

    def get_exporter(self):
        from .exporter import SatoriMessageExporter

        return SatoriMessageExporter()

    def get_fetcher(self):
        from .target import SatoriTargetFetcher

        return SatoriTargetFetcher()
