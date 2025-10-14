from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.loader import BaseLoader


class Loader(BaseLoader):
    def get_adapter(self) -> SupportAdapter:
        return SupportAdapter.mail

    def get_builder(self):
        from .builder import MailMessageBuilder

        return MailMessageBuilder()

    def get_exporter(self):
        from .exporter import MailMessageExporter

        return MailMessageExporter()
