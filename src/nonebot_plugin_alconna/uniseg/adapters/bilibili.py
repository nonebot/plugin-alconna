from typing import cast

from nonebot.adapters import Bot, Event, Message, MessageSegment

from ..segment import Text
from ..export import Target, MessageExporter, export


class BilibiliMessageExporter(MessageExporter):
    def get_message_type(self):
        from nonebot.adapters.bilibili.message import Message

        return Message

    @classmethod
    def get_adapter(cls) -> str:
        return "BilibiliLive"

    def get_message_id(self, event: Event) -> str:
        from nonebot.adapters.bilibili.event import MessageEvent

        assert isinstance(event, MessageEvent)
        return str(event.session_id)

    @export
    async def text(self, seg: Text, bot: Bot) -> MessageSegment:
        msg = self.get_message_type()
        ms = msg.get_segment_class()  # type: ignore

        return ms.danmu(seg.text)

    async def send_to(self, target: Target, bot: Bot, message: Message):
        from nonebot.adapters.bilibili.adapter import Adapter

        adapter: Adapter = cast(Adapter, bot.adapter)
        return await adapter.bili.send(str(message), bot.self_id)
