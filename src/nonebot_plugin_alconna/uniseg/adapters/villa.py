from datetime import datetime
from typing import TYPE_CHECKING

from nonebot.adapters import Bot

from ..segment import At, Text, AtAll, Image, Reply
from ..export import MessageExporter, SerializeFailed, export

if TYPE_CHECKING:
    from nonebot.adapters.villa.message import MessageSegment


class VillaMessageExporter(MessageExporter["MessageSegment"]):
    @classmethod
    def get_adapter(cls) -> str:
        return "Villa"

    def get_message_type(self):
        from nonebot.adapters.villa.message import Message

        return Message

    @export
    async def text(self, seg: Text, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.text(seg.text)

    @export
    async def at(self, seg: At, bot: Bot) -> "MessageSegment":
        ms = self.segment_class
        if seg.type == "user":
            return ms.mention_user(int(seg.target), seg.display)
        elif seg.type == "channel":
            villa_id, room_id = seg.target.split(":", 1)
            return ms.room_link(int(villa_id), int(room_id), seg.display)
        else:
            raise SerializeFailed(f"Invalid At segment: {seg!r}")

    @export
    async def at_all(self, seg: AtAll, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.mention_all()

    @export
    async def image(self, seg: Image, bot: Bot) -> "MessageSegment":
        ms = self.segment_class
        if seg.url:
            return ms.image(seg.url)
        else:
            raise SerializeFailed(f"Invalid image segment: {seg!r}")

    @export
    async def reply(self, seg: Reply, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.quote(seg.id, int(datetime.now().timestamp()))
