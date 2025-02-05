from nonebot.adapters.minecraft.model import TextColor
from nonebot.adapters.minecraft.message import MessageSegment

from nonebot_plugin_alconna.uniseg.segment import Text
from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.builder import MessageBuilder, build


class MinecraftMessageBuilder(MessageBuilder):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.minecraft

    def get_styles(self, data: dict):
        styles = []
        if "color" in data and data["color"] and data["color"] != TextColor.WHITE:
            styles.append(data["color"])
        if data.get("bold"):
            styles.append("bold")
        if data.get("italic"):
            styles.append("italic")
        if data.get("underlined"):
            styles.append("underlined")
        if data.get("strikethrough"):
            styles.append("strikethrough")
        if data.get("obfuscated"):
            styles.append("obfuscated")
        return styles

    @build("text")
    def text(self, seg: MessageSegment):
        text = Text(seg.data["text"])
        _len = len(seg.data["text"])
        text.mark(0, _len, *self.get_styles(seg.data))
        return text

    @build("title")
    def title(self, seg: MessageSegment):
        text = Text(seg.data["title"]["text"])
        _len = len(seg.data["title"]["text"])
        return text.mark(0, _len, "title", *self.get_styles(seg.data["title"]))

    @build("actionbar")
    def actionbar(self, seg: MessageSegment):
        text = Text(seg.data["text"])
        _len = len(seg.data["text"])
        text.mark(0, _len, "actionbar", *self.get_styles(seg.data))
        return text
