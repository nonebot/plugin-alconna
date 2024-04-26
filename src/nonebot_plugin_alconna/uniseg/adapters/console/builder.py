from nonebot.adapters.console.message import MessageSegment

from nonebot_plugin_alconna.uniseg.segment import Text, Emoji
from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.builder import MessageBuilder, build


class ConsoleMessageBuilder(MessageBuilder):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.console

    @build("markup")
    def markup(self, seg: MessageSegment):
        return Text(seg.data["markup"]).mark(0, len(seg.data["markup"]), "markup", seg.data["style"])

    @build("markdown")
    def markdown(self, seg: MessageSegment):
        return Text(seg.data["markup"]).mark(0, len(seg.data["markup"]), "markdown", seg.data["code_theme"])

    @build("emoji")
    def emoji(self, seg: MessageSegment):
        return Emoji(seg.data["name"])
