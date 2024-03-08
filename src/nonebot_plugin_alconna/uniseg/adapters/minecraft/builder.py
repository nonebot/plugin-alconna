from nonebot.adapters.minecraft.model import TextColor
from nonebot.adapters.minecraft.message import MessageSegment

from nonebot_plugin_alconna.uniseg.segment import Text
from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.builder import MessageBuilder, build


class MinecraftMessageBuilder(MessageBuilder):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.minecraft

    @build("text")
    def text(self, seg: MessageSegment):
        text = Text(seg.data["text"])
        _len = len(seg.data["text"])
        styles = []
        if "color" in seg.data and seg.data["color"] != TextColor.WHITE:
            styles.append(seg.data["color"])
        if "bold" in seg.data and seg.data["bold"]:
            styles.append("bold")
        if "italic" in seg.data and seg.data["italic"]:
            styles.append("italic")
        if "underlined" in seg.data and seg.data["underlined"]:
            styles.append("underlined")
        if "strikethrough" in seg.data and seg.data["strikethrough"]:
            styles.append("strikethrough")
        if "obfuscated" in seg.data and seg.data["obfuscated"]:
            styles.append("obfuscated")
        text.mark(0, _len, *styles)
        return text

    @build("title")
    def title(self, seg: MessageSegment):
        return Text(seg.data["title"]).mark(0, len(seg.data["title"]), "title")

    @build("actionbar")
    def actionbar(self, seg: MessageSegment):
        text = Text(seg.data["text"])
        _len = len(seg.data["text"])
        styles = ["actionbar"]
        if "color" in seg.data and seg.data["color"] != TextColor.WHITE:
            styles.append(seg.data["color"])
        if "bold" in seg.data and seg.data["bold"]:
            styles.append("bold")
        if "italic" in seg.data and seg.data["italic"]:
            styles.append("italic")
        if "underlined" in seg.data and seg.data["underlined"]:
            styles.append("underlined")
        if "strikethrough" in seg.data and seg.data["strikethrough"]:
            styles.append("strikethrough")
        if "obfuscated" in seg.data and seg.data["obfuscated"]:
            styles.append("obfuscated")
        text.mark(0, _len, *styles)
        return text
