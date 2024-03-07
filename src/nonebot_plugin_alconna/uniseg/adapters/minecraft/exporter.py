from typing import Union

from nonebot.adapters import Bot, Event
from nonebot.adapters.minecraft.bot import Bot as MinecraftBot
from nonebot.adapters.minecraft.event.base import MessageEvent
from nonebot.adapters.minecraft.message import Message, MessageSegment

from nonebot_plugin_alconna.uniseg.segment import Text
from nonebot_plugin_alconna.uniseg.exporter import Target, SupportAdapter, MessageExporter, export


class MinecraftMessageExporter(MessageExporter[Message]):
    def get_message_type(self):
        return Message

    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.minecraft

    def get_message_id(self, event: Event) -> str:
        assert isinstance(event, MessageEvent)
        return str(id(event))

    @export
    async def text(self, seg: Text, bot: Bot) -> "MessageSegment":
        return MessageSegment.text(seg.text)

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: Message):
        assert isinstance(bot, MinecraftBot)
        return await bot.send_msg(message=message)  # type: ignore
