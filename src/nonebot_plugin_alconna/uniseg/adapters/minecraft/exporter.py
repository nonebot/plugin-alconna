from typing import Union

from nonebot.adapters import Bot, Event
from nonebot.adapters.minecraft.model import TextColor
from nonebot.adapters.minecraft.bot import Bot as MinecraftBot
from nonebot.adapters.minecraft.event.base import MessageEvent
from nonebot.adapters.minecraft.message import Message, MessageSegment

from nonebot_plugin_alconna.uniseg.segment import Text
from nonebot_plugin_alconna.uniseg.constraint import SupportScope
from nonebot_plugin_alconna.uniseg.exporter import Target, SupportAdapter, MessageExporter, export

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

for color in TextColor.__members__.values():
    STYLE_TYPE_MAP[color.value] = color.value


class MinecraftMessageExporter(MessageExporter[Message]):
    def get_message_type(self):
        return Message

    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.minecraft

    def get_message_id(self, event: Event) -> str:
        assert isinstance(event, MessageEvent)
        return str(id(event))

    def get_target(self, event: Event, bot: Union[Bot, None] = None) -> Target:
        return Target(
            event.get_user_id(),
            adapter=self.get_adapter(),
            self_id=bot.self_id if bot else None,
            scope=SupportScope.minecraft,
        )

    @export
    async def text(self, seg: Text, bot: Bot) -> "MessageSegment":
        if seg.extract_most_style() == "title":
            return MessageSegment.title(seg.text)
        styles = [STYLE_TYPE_MAP[s] for s in seg.styles[(0, len(seg.text))] if s in STYLE_TYPE_MAP]
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
        if seg.extract_most_style() == "actionbar":
            return MessageSegment.actionbar(seg.text, **kwargs)
        return MessageSegment.text(seg.text, **kwargs)

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: Message):
        assert isinstance(bot, MinecraftBot)
        return await bot.send_msg(message=message)  # type: ignore
