from datetime import datetime
from typing import TYPE_CHECKING

from tarina import lang
from nonebot.adapters import Bot

from ..export import MessageExporter, SerializeFailed, export
from ..segment import At, Text, AtAll, Image, Reply, Reference

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
        if seg.flag == "user":
            return ms.mention_user(int(seg.target), seg.display)
        elif seg.flag == "channel":
            villa_id, room_id = seg.target.split(":", 1)
            return ms.room_link(int(villa_id), int(room_id), seg.display)
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="at", seg=seg))

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
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="image", seg=seg))

    @export
    async def reply(self, seg: Reply, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.quote(seg.id, int(datetime.now().timestamp()))

    @export
    async def reference(self, seg: Reference, bot: Bot) -> "MessageSegment":
        ms = self.segment_class
        if not seg.id:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="post", seg=seg))
        return ms.post(seg.id)
