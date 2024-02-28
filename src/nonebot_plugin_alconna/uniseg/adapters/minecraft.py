from typing import TYPE_CHECKING, Union

from nonebot.adapters import Bot, Event, Message

from ..segment import Text
from ..export import Target, SupportAdapter, MessageExporter, export

if TYPE_CHECKING:
    from nonebot.adapters.minecraft.message import MessageSegment


class MinecraftMessageExporter(MessageExporter["MessageSegment"]):
    def get_message_type(self):
        from nonebot.adapters.minecraft.message import Message

        return Message

    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.minecraft

    def get_message_id(self, event: Event) -> str:
        from nonebot.adapters.minecraft.event.base import MessageEvent

        assert isinstance(event, MessageEvent)
        return str(id(event))

    @export
    async def text(self, seg: Text, bot: Bot) -> "MessageSegment":
        ms = self.segment_class
        return ms.text(seg.text)

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: Message):
        from nonebot.adapters.minecraft.bot import Bot as MinecraftBot

        assert isinstance(bot, MinecraftBot)

        return await bot.send_msg(message=message)  # type: ignore
