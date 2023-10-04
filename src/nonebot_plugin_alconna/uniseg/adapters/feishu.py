from pathlib import Path
from typing import TYPE_CHECKING, Union

from tarina import lang
from nonebot.adapters import Bot
from nonebot.internal.driver import Request

from ..export import MessageExporter, SerializeFailed, export
from ..segment import At, File, Text, Audio, Image, Reply, Voice

if TYPE_CHECKING:
    from nonebot.adapters.feishu.message import MessageSegment


class FeishuMessageExporter(MessageExporter["MessageSegment"]):
    def get_message_type(self):
        from nonebot.adapters.feishu.message import Message

        return Message

    @classmethod
    def get_adapter(cls) -> str:
        return "Feishu"

    @export
    async def text(self, seg: Text, bot: Bot) -> "MessageSegment":
        ms = self.segment_class
        return ms.text(seg.text)

    @export
    async def at(self, seg: At, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.at(seg.target)

    @export
    async def image(self, seg: Image, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        if seg.id:
            return ms.image(seg.id)
        elif seg.url:
            resp = await bot.adapter.request(Request("GET", seg.url))
            image = resp.content
        elif seg.path:
            image = Path(seg.path).read_bytes()
        elif seg.raw:
            image = seg.raw
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="image", seg=seg))
        data = {"image_type": "message"}
        files = {"image": ("file", image)}
        params = {"method": "POST", "data": data, "files": files}
        result = await bot.call_api("im/v1/images", **params)
        file_key = result["image_key"]
        return ms.image(file_key)

    @export
    async def audio(self, seg: Union[Voice, Audio], bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        name = seg.__class__.__name__.lower()
        if seg.id:
            return ms.audio(seg.id)
        elif seg.url:
            resp = await bot.adapter.request(Request("GET", seg.url))
            audio = resp.content
        elif seg.path:
            audio = Path(seg.path).read_bytes()
        elif seg.raw:
            audio = seg.raw
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type=name, seg=seg))
        data = {"file_type": "stream", "file_name": seg.name}
        files = {"file": ("file", audio)}
        params = {"method": "POST", "data": data, "files": files}
        result = await bot.call_api("im/v1/files", **params)
        file_key = result["file_key"]
        return ms.audio(file_key)

    @export
    async def file(self, seg: File, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        if seg.id:
            return ms.file(seg.id)
        elif seg.raw and seg.name:
            data = {"file_type": "stream", "file_name": seg.name}
            files = {"file": ("file", seg.raw)}
            params = {"method": "POST", "data": data, "files": files}
            result = await bot.call_api("im/v1/files", **params)
            file_key = result["file_key"]
            return ms.file(file_key)
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="file", seg=seg))

    @export
    async def reply(self, seg: Reply, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms("reply", {"message_id": seg.id})
