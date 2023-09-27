from typing import TYPE_CHECKING

from nonebot.adapters import Bot

from ..export import MessageExporter, export
from ..segment import At, Text, AtAll, Image

if TYPE_CHECKING:
    from nonebot.adapters.ding.message import MessageSegment


class DingMessageExporter(MessageExporter["MessageSegment"]):
    def get_message_type(self):
        from nonebot.adapters.ding.message import Message

        return Message

    @classmethod
    def get_adapter(cls) -> str:
        return "Ding"

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
