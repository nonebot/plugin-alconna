from pathlib import Path
from typing import TYPE_CHECKING, Union

from tarina import lang
from nonebot.adapters import Bot
from nonebot.internal.driver import Request

from ..export import MessageExporter, SerializeFailed, export
from ..segment import At, Card, Text, AtAll, Audio, Emoji, Image, Reply, Video, Voice

if TYPE_CHECKING:
    from nonebot.adapters.onebot.v11.message import MessageSegment


class Onebot11MessageExporter(MessageExporter["MessageSegment"]):
    def get_message_type(self):
        from nonebot.adapters.onebot.v11.message import Message

        return Message

    @classmethod
    def get_adapter(cls) -> str:
        return "OneBot V11"

    @export
    async def text(self, seg: Text, bot: Bot) -> "MessageSegment":
        ms = self.segment_class
        return ms.text(seg.text)

    @export
    async def at(self, seg: At, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.at(seg.target)

    @export
    async def at_all(self, seg: AtAll, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.at("all")

    @export
    async def emoji(self, seg: Emoji, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.face(int(seg.id))

    @export
    async def media(self, seg: Union[Image, Voice, Video, Audio], bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        name = seg.__class__.__name__.lower()
        method = {
            "image": ms.image,
            "voice": ms.record,
            "video": ms.video,
            "audio": ms.record,
        }[name]
        if seg.raw:
            return method(seg.raw_bytes)
        elif seg.path:
            return method(Path(seg.path))
        elif seg.url:
            resp = await bot.adapter.request(Request("GET", seg.url))
            return method(resp.content)
        elif seg.id:
            return method(seg.id)
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type=name, seg=seg))

    @export
    async def card(self, seg: Card, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.xml(seg.raw) if seg.flag == "xml" else ms.json(seg.raw)

    @export
    async def reply(self, seg: Reply, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.reply(int(seg.id))
