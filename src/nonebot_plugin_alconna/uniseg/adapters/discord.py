from pathlib import Path
from typing import TYPE_CHECKING, Union

from tarina import lang
from nonebot.adapters import Bot
from nonebot.internal.driver import Request

from ..export import MessageExporter, SerializeFailed, export
from ..segment import At, File, Text, AtAll, Audio, Emoji, Image, Reply, Video, Voice

if TYPE_CHECKING:
    from nonebot.adapters.discord.message import MessageSegment


class DiscordMessageExporter(MessageExporter["MessageSegment"]):
    def get_message_type(self):
        from nonebot.adapters.discord.message import Message

        return Message

    @classmethod
    def get_adapter(cls) -> str:
        return "Discord"

    @export
    async def text(self, seg: Text, bot: Bot) -> "MessageSegment":
        ms = self.segment_class
        return ms.text(seg.text)

    @export
    async def at(self, seg: At, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        if seg.flag == "role":
            return ms.mention_role(int(seg.target))
        elif seg.flag == "channel":
            return ms.mention_channel(int(seg.target))
        else:
            return ms.mention_user(int(seg.target))

    @export
    async def at_all(self, seg: AtAll, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.mention_everyone()

    @export
    async def emoji(self, seg: Emoji, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.custom_emoji(seg.name or "", seg.id)

    @export
    async def media(self, seg: Union[Image, Voice, Video, Audio, File], bot: Bot) -> "MessageSegment":
        ms = self.segment_class
        name = seg.__class__.__name__.lower()

        if seg.raw and (seg.id or seg.name):
            return ms.attachment(seg.id or seg.name, content=seg.raw_bytes)
        elif seg.path:
            path = Path(seg.path)
            return ms.attachment(path.name, content=path.read_bytes())
        elif seg.url and (seg.id or seg.name):
            resp = await bot.adapter.request(Request("GET", seg.url))
            return ms.attachment(
                seg.id or seg.name,
                content=resp.content,  # type: ignore
            )
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type=name, seg=seg))

    @export
    async def reply(self, seg: Reply, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.reference(seg.origin or int(seg.id))
