from typing import TYPE_CHECKING, Union

from tarina import lang
from nonebot.adapters import Bot

from ..export import MessageExporter, SerializeFailed, export
from ..segment import At, File, Text, AtAll, Audio, Image, Reply, Video, Voice

if TYPE_CHECKING:
    from nonebot.adapters.satori.message import MessageSegment


class SatoriMessageExporter(MessageExporter["MessageSegment"]):
    def get_message_type(self):
        from nonebot.adapters.satori.message import Message

        return Message

    @classmethod
    def get_adapter(cls) -> str:
        return "Telegram"

    @export
    async def text(self, seg: Text, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        if not seg.style:
            return ms.text(seg.text)
        if seg.style == "br" or seg.text == "\n":
            return ms.br()
        if seg.style in ("p", "paragraph"):
            return ms.paragraph(seg.text)
        return ms.entity(seg.text, seg.style)

    @export
    async def at(self, seg: At, bot: Bot) -> "MessageSegment":
        ms = self.segment_class
        if seg.flag == "role":
            return ms.at_role(seg.target, seg.display)
        if seg.flag == "channel":
            return ms.sharp(seg.target, seg.display)
        return ms.at(seg.target, seg.display)

    @export
    async def at_all(self, seg: AtAll, bot: Bot) -> "MessageSegment":
        ms = self.segment_class
        return ms.at_all(seg.here)

    @export
    async def res(self, seg: Union[Image, Voice, Video, Audio], bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        name = seg.__class__.__name__.lower()
        method = {
            "image": ms.image,
            "voice": ms.audio,
            "video": ms.video,
            "audio": ms.audio,
        }[name]
        if seg.id or seg.url:
            return method(seg.id or seg.url)
        raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type=name, seg=seg))

    @export
    async def file(self, seg: File, bot: Bot) -> "MessageSegment":
        ms = self.segment_class
        if seg.id:
            return ms.file(seg.id)
        raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="file", seg=seg))

    @export
    async def reply(self, seg: Reply, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.quote(seg.id, content=seg.msg)  # type: ignore
