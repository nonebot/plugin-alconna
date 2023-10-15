from pathlib import Path
from typing import TYPE_CHECKING

from tarina import lang
from nonebot.adapters import Bot

from ..segment import At, Text, AtAll, Emoji, Image, Reply
from ..export import MessageExporter, SerializeFailed, export

if TYPE_CHECKING:
    from nonebot.adapters.qqguild.message import MessageSegment


class QQGuildMessageExporter(MessageExporter["MessageSegment"]):
    @classmethod
    def get_adapter(cls) -> str:
        return "QQ Guild"

    def get_message_type(self):
        from nonebot.adapters.qqguild.message import Message

        return Message

    @export
    async def text(self, seg: Text, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.text(seg.text)

    @export
    async def at(self, seg: At, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        if seg.target == "channel":
            return ms.mention_channel(int(seg.target))
        elif seg.target == "user":
            return ms.mention_user(int(seg.target))
        else:
            raise SerializeFailed(
                lang.require("nbp-uniseg", "failed_segment").format(
                    adapter="qqguild", seg=seg, target="mention"
                )
            )

    @export
    async def at_all(self, seg: AtAll, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.mention_everyone()

    @export
    async def emoji(self, seg: Emoji, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.emoji(seg.id)

    @export
    async def image(self, seg: Image, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        if seg.url:
            return ms.image(seg.url)
        elif seg.raw or seg.path:
            return ms.file_image(seg.raw_bytes or Path(seg.path))
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="image", seg=seg))

    @export
    async def reply(self, seg: Reply, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.reference(seg.id)
