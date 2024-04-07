from typing import Union, cast

from nonebot.adapters import Bot, Event
from nonebot.adapters.bilibili.adapter import Adapter  # type: ignore
from nonebot.adapters.bilibili.event import MessageEvent  # type: ignore
from nonebot.adapters.bilibili.message import Message, MessageSegment  # type: ignore

from nonebot_plugin_alconna.uniseg.segment import Text
from nonebot_plugin_alconna.uniseg.constraint import SupportScope, SupportAdapter
from nonebot_plugin_alconna.uniseg.exporter import Target, MessageExporter, export


class BilibiliMessageExporter(MessageExporter["Message"]):
    def get_message_type(self):
        return Message

    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.bilibili

    def get_target(self, event: Event, bot: Union[Bot, None] = None) -> Target:
        return Target(
            event.get_user_id(),
            adapter=self.get_adapter(),
            self_id=bot.self_id if bot else None,
            scope=SupportScope.bilibili,
        )

    def get_message_id(self, event: Event) -> str:
        assert isinstance(event, MessageEvent)
        return str(event.session_id)  # type: ignore

    @export
    async def text(self, seg: Text, bot: Bot) -> MessageSegment:
        return MessageSegment.danmu(seg.text)

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: Message):
        adapter: Adapter = cast(Adapter, bot.adapter)
        return await adapter.bili.send(str(message), bot.self_id)
