from nonebot.adapters.minecraft.message import MessageSegment

from nonebot_plugin_alconna.uniseg import Text
from nonebot_plugin_alconna.typings import TextSegmentPattern

STYLE_TYPE_MAP = {
    "b": "bold",
    "strong": "bold",
    "bold": "bold",
    "i": "italic",
    "em": "italic",
    "italic": "italic",
    "u": "underline",
    "ins": "underline",
    "underline": "underline",
    "s": "strikethrough",
    "del": "strikethrough",
    "strike": "strikethrough",
    "strikethrough": "strikethrough",
    "obf": "obfuscated",
    "obfuscated": "obfuscated",
}


def title(self, x: Text):
    if x.extract_most_style() == "title":
        return MessageSegment.title(x.text)


def actionbar(sef, x: Text):
    if x.extract_most_style() == "actionbar":
        styles = [STYLE_TYPE_MAP[s] for s in x.styles[(0, len(x.text))] if s in STYLE_TYPE_MAP]
        kwargs = {}
        for style in styles:
            if style == "bold":
                kwargs["bold"] = True
            elif style == "italic":
                kwargs["italic"] = True
            elif style == "underline":
                kwargs["underlined"] = True
            elif style == "strikethrough":
                kwargs["strikethrough"] = True
            elif style == "obfuscated":
                kwargs["obfuscated"] = True
            else:
                kwargs["color"] = style
        return MessageSegment.actionbar(x.text, **kwargs)


Title = TextSegmentPattern("title", MessageSegment, MessageSegment.title, title)
ActionBar = TextSegmentPattern("actionbar", MessageSegment, MessageSegment.actionbar, actionbar)
