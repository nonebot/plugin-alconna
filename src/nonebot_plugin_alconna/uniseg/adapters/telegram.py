from pathlib import Path
from typing import TYPE_CHECKING, Union

from tarina import lang
from nonebot.adapters import Bot

from ..export import MessageExporter, SerializeFailed, export
from ..segment import At, File, Text, Audio, Emoji, Image, Reply, Video, Voice

if TYPE_CHECKING:
    from nonebot.adapters.telegram.message import MessageSegment


class TelegramMessageExporter(MessageExporter["MessageSegment"]):
    def get_message_type(self):
        from nonebot.adapters.telegram.message import Message

        return Message

    @classmethod
    def get_adapter(cls) -> str:
        return "Telegram"

    @export
    async def text(self, seg: Text, bot: Bot) -> "MessageSegment":
        from nonebot.adapters.telegram.message import Entity

        if not seg.style:
            return Entity.text(seg.text)
        else:
            return Entity(seg.style, {"text": seg.text})

    @export
    async def at(self, seg: At, bot: Bot) -> "MessageSegment":
        from nonebot.adapters.telegram.message import Entity

        return (
            Entity.mention(f"{seg.target} ")
            if seg.target.startswith("@")
            else Entity.text_link("用户 ", f"tg://user?id={seg.target}")
        )

    @export
    async def emoji(self, seg: Emoji, bot: Bot) -> "MessageSegment":
        from nonebot.adapters.telegram.message import Entity

        return Entity.custom_emoji(seg.name, seg.id)  # type: ignore

    @export
    async def media(self, seg: Union[Image, Voice, Video, Audio, File], bot: Bot) -> "MessageSegment":
        from nonebot.adapters.telegram.message import File as TgFile

        name = seg.__class__.__name__.lower()
        method = {
            "image": TgFile.photo,
            "voice": TgFile.voice,
            "video": TgFile.video,
            "audio": TgFile.audio,
            "file": TgFile.document,
        }[name]
        if seg.id or seg.url:
            return method(seg.id or seg.url)
        elif seg.path:
            return method(Path(seg.path).read_bytes())
        elif seg.raw:
            return method(seg.raw_bytes)
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type=name, seg=seg))

    @export
    async def reply(self, seg: Reply, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms("reply", {"message_id": seg.id})  # type: ignore
