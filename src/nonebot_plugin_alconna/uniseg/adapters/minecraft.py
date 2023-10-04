from typing import TYPE_CHECKING, Union

from tarina import lang
from nonebot.adapters import Bot

from ..segment import Text, Image, Video
from ..export import MessageExporter, SerializeFailed, export

if TYPE_CHECKING:
    from nonebot.adapters.minecraft.message import MessageSegment


class MinecraftMessageExporter(MessageExporter["MessageSegment"]):
    def get_message_type(self):
        from nonebot.adapters.minecraft.message import Message

        return Message

    @classmethod
    def get_adapter(cls) -> str:
        return "Minecraft"

    @export
    async def text(self, seg: Text, bot: Bot) -> "MessageSegment":
        ms = self.segment_class
        return ms.text(seg.text)

    @export
    async def media(self, seg: Union[Image, Video], bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        name = seg.__class__.__name__.lower()
        method = {
            "image": ms.image,
            "video": ms.video,
        }[name]
        if seg.id or seg.url:
            return method(seg.id or seg.url)  # type: ignore
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type=name, seg=seg))
