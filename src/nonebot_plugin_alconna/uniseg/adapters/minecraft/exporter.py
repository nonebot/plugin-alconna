from typing import Union

from tarina import lang
from nonebot.adapters import Bot, Event
from nonebot.adapters.minecraft.bot import Bot as MinecraftBot
from nonebot.adapters.minecraft.event.base import MessageEvent
from nonebot.adapters.minecraft.message import Message, MessageSegment
from nonebot.adapters.minecraft.model import TextColor, ClickEvent, HoverEvent, ClickAction, HoverAction, BaseComponent

from nonebot_plugin_alconna.uniseg.constraint import SupportScope
from nonebot_plugin_alconna.uniseg.segment import Text, Button, Keyboard
from nonebot_plugin_alconna.uniseg.exporter import Target, SupportAdapter, MessageExporter, SerializeFailed, export

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
    async def text(self, seg: Text, bot: Union[Bot, None]) -> "MessageSegment":
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
        if seg.extract_most_style() == "title":
            return MessageSegment.title(BaseComponent(text=seg.text, **kwargs))
        return MessageSegment.text(seg.text, **kwargs)

    @export
    async def button(self, seg: Button, bot: Union[Bot, None]):
        label = Text(seg.label) if isinstance(seg.label, str) else seg.label
        styles = [STYLE_TYPE_MAP[s] for s in label.styles[(0, len(label.text))] if s in STYLE_TYPE_MAP]
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
        if seg.clicked_label:
            kwargs["hover_event"] = HoverEvent(
                action=HoverAction.SHOW_TEXT, base_component_list=[BaseComponent(text=seg.clicked_label)]
            )
        if seg.flag == "link":
            return MessageSegment.text(
                label.text, **kwargs, click_event=ClickEvent(action=ClickAction.OPEN_URL, value=seg.url)
            )
        if seg.flag == "input":
            return MessageSegment.text(
                label.text, **kwargs, click_event=ClickEvent(action=ClickAction.SUGGEST_COMMAND, value=seg.text)
            )
        if seg.flag == "enter":
            return MessageSegment.text(
                label.text, **kwargs, click_event=ClickEvent(action=ClickAction.RUN_COMMAND, value=seg.text)
            )
        raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="button", seg=seg))

    @export
    async def keyboard(self, seg: Keyboard, bot: Union[Bot, None]):
        if seg.children:
            return [await self.button(child, bot) for child in seg.children]
        return MessageSegment.text("")

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: Message, **kwargs):
        assert isinstance(bot, MinecraftBot)
        if isinstance(target, Event):
            return await bot.send(target, message, **kwargs)  # type: ignore
        return await bot.send_msg(message=message)  # type: ignore
