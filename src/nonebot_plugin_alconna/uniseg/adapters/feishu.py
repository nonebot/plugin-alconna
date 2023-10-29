from pathlib import Path
from typing import TYPE_CHECKING, Union

from tarina import lang
from nonebot.adapters import Bot, Message
from nonebot.internal.driver import Request

from ..segment import At, File, Text, Audio, Image, Reply, Voice
from ..export import Target, MessageExporter, SerializeFailed, export

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
            image = seg.raw_bytes
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="image", seg=seg))
        data = {"image_type": "message"}
        files = {"image": ("file", image)}
        params = {"method": "POST", "data": data, "files": files}
        result = await bot.call_api("im/v1/images", **params)
        file_key = result["image_key"]
        return ms.image(file_key)

    @export
    async def media(self, seg: Union[Voice, Audio, File], bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        name = seg.__class__.__name__.lower()
        method = {
            "voice": ms.audio,
            "audio": ms.audio,
            "file": ms.file,
        }[name]
        if seg.id:
            return method(seg.id)
        elif seg.url:
            resp = await bot.adapter.request(Request("GET", seg.url))
            raw = resp.content
        elif seg.path:
            raw = Path(seg.path).read_bytes()
        elif seg.raw:
            raw = seg.raw_bytes
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type=name, seg=seg))
        data = {"file_type": "stream", "file_name": seg.name}
        files = {"file": ("file", raw)}
        params = {"method": "POST", "data": data, "files": files}
        result = await bot.call_api("im/v1/files", **params)
        file_key = result["file_key"]
        return method(file_key)

    @export
    async def reply(self, seg: Reply, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms("reply", {"message_id": seg.id})  # type: ignore

    async def send_to(self, target: Target, bot: Bot, message: Message):
        from nonebot.adapters.feishu.bot import Bot as FeishuBot
        from nonebot.adapters.feishu.message import MessageSerializer

        assert isinstance(bot, FeishuBot)

        if target.private:
            receive_id, receive_id_type = target.id, "open_id"
        else:
            receive_id, receive_id_type = target.id, "chat_id"

        msg_type, content = MessageSerializer(message).serialize()

        params = {
            "method": "POST",
            "query": {"receive_id_type": receive_id_type},
            "body": {
                "receive_id": receive_id,
                "content": content,
                "msg_type": msg_type,
            },
        }

        return await bot.call_api("im/v1/messages", **params)
