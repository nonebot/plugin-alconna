from typing import TYPE_CHECKING

from nonebot.adapters import Bot, Event, Message

from ..segment import At, Text, AtAll, Image
from ..export import Target, MessageExporter, export

if TYPE_CHECKING:
    from nonebot.adapters.ding.message import MessageSegment


class DingMessageExporter(MessageExporter["MessageSegment"]):
    def get_message_type(self):
        from nonebot.adapters.ding.message import Message

        return Message

    @classmethod
    def get_adapter(cls) -> str:
        return "Ding"

    def get_target(self, event: Event) -> Target:
        from nonebot.adapters.ding.event import MessageEvent, ConversationType

        if isinstance(event, MessageEvent):
            if event.conversationType == ConversationType.private:
                return Target(event.senderId, private=True)
            return Target(event.conversationId)
        raise NotImplementedError

    def get_message_id(self, event: Event) -> str:
        from nonebot.adapters.ding.event import MessageEvent

        assert isinstance(event, MessageEvent)
        return str(event.msgId)

    @export
    async def text(self, seg: Text, bot: Bot) -> "MessageSegment":
        ms = self.segment_class
        return ms.text(seg.text)

    @export
    async def at(self, seg: At, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.atDingtalkIds(seg.target)

    @export
    async def at_all(self, seg: AtAll, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.atAll()

    @export
    async def image(self, seg: Image, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        assert seg.url, "ding image segment must have url"
        return ms.image(seg.url)

    async def send_to(self, target: Target, bot: Bot, message: Message):
        raise NotImplementedError
