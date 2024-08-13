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
        if "bold" in data and data["bold"]:
            styles.append("bold")
        if "italic" in data and data["italic"]:
            styles.append("italic")
        if "underlined" in data and data["underlined"]:
            styles.append("underlined")
        if "strikethrough" in data and data["strikethrough"]:
            styles.append("strikethrough")
        if "obfuscated" in data and data["obfuscated"]:
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
