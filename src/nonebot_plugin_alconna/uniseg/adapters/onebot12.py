from typing import TYPE_CHECKING, Union

from nonebot.adapters import Bot

from ..export import MessageExporter, SerializeFailed, export
from ..segment import At, File, Text, AtAll, Audio, Image, Reply, Video, Voice

if TYPE_CHECKING:
    from nonebot.adapters.onebot.v12.message import MessageSegment


class Onebot12MessageExporter(MessageExporter["MessageSegment"]):
    def get_message_type(self):
        from nonebot.adapters.onebot.v12.message import Message

        return Message

    @classmethod
    def get_adapter(cls) -> str:
        return "OneBot V12"

    @export
    async def text(self, seg: Text, bot: Bot) -> "MessageSegment":
        ms = self.segment_class
        return ms.text(seg.text)

    @export
    async def at(self, seg: At, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.mention(seg.target)

    @export
    async def at_all(self, seg: AtAll, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.mention_all()

    @export
    async def media(self, seg: Union[Image, Voice, Video, Audio], bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        name = seg.__class__.__name__.lower()
        method = {
            "image": ms.image,
            "voice": ms.voice,
            "video": ms.video,
            "audio": ms.audio,
        }[name]
        if seg.id:
            return method(seg.id)
        elif seg.url:
            resp = await bot.upload_file(type="url", name=seg.name, url=seg.url)
            return method(resp["file_id"])
        elif seg.path:
            resp = await bot.upload_file(type="path", name=seg.name, path=str(seg.path))
            return method(resp["file_id"])
        elif seg.raw:
            resp = await bot.upload_file(type="data", name=seg.name, data=seg.raw)
            return method(resp["file_id"])
        else:
            raise SerializeFailed(f"Invalid {name} segment: {seg!r}")

    @export
    async def file(self, seg: File, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        if seg.id:
            return ms.file(seg.id)
        elif seg.raw:
            resp = await bot.upload_file(type="data", name=seg.name or "file", data=seg.raw)
            return ms.file(resp["file_id"])
        else:
            raise SerializeFailed(f"Invalid file segment: {seg!r}")

    @export
    async def reply(self, seg: Reply, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.reply(seg.id)
