from typing import TYPE_CHECKING, Union

from tarina import lang
from nonebot.adapters import Bot

from ..export import MessageExporter, SerializeFailed, export
from ..segment import At, Card, File, Text, AtAll, Audio, Emoji, Image, Reply, Voice

if TYPE_CHECKING:
    from nonebot.adapters.mirai2.message import MessageSegment


class MiraiMessageExporter(MessageExporter["MessageSegment"]):
    @classmethod
    def get_adapter(cls) -> str:
        return "mirai2"

    def get_message_type(self):
        from nonebot.adapters.mirai2.message import MessageChain

        return MessageChain

    @export
    async def text(self, seg: Text, bot: Bot) -> "MessageSegment":
        ms = self.segment_class
        return ms.plain(seg.text)

    @export
    async def at(self, seg: At, bot: Bot) -> "MessageSegment":
        ms = self.segment_class
        return ms.at(int(seg.target))

    @export
    async def at_all(self, seg: AtAll, bot: Bot) -> "MessageSegment":
        ms = self.segment_class
        return ms.at_all()

    @export
    async def emoji(self, seg: Emoji, bot: Bot) -> "MessageSegment":
        ms = self.segment_class
        return ms.face(int(seg.id), seg.name)

    @export
    async def media(self, seg: Union[Image, Voice, Audio], bot: Bot) -> "MessageSegment":
        ms = self.segment_class
        name = seg.__class__.__name__.lower()
        method = {
            "image": ms.image,
            "voice": ms.voice,
            "audio": ms.voice,
        }[name]
        if seg.id:
            return method(seg.id)
        elif seg.url:
            return method(url=seg.url)
        elif seg.path:
            return method(path=str(seg.path))
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type=name, seg=seg))

    @export
    async def file(self, seg: File, bot: Bot) -> "MessageSegment":
        ms = self.segment_class
        return ms.file(seg.id, seg.name, 0)

    @export
    async def card(self, seg: Card, bot: Bot) -> "MessageSegment":
        ms = self.segment_class
        return ms.xml(seg.raw) if seg.flag == "xml" else ms.app(seg.raw)

    @export
    async def reply(self, seg: Reply, bot: Bot) -> "MessageSegment":
        from nonebot.adapters.mirai2.message import MessageType

        ms = self.segment_class
        return ms(MessageType.QUOTE, id=seg.id)
