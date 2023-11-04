from pathlib import Path
from typing import TYPE_CHECKING, Any, Union

from tarina import lang
from nonebot.internal.driver import Request
from nonebot.adapters import Bot, Event, Message

from ..export import Target, MessageExporter, SerializeFailed, export
from ..segment import At, File, Text, AtAll, Audio, Image, Reply, Voice

if TYPE_CHECKING:
    from nonebot.adapters.feishu.message import MessageSegment


class FeishuMessageExporter(MessageExporter["MessageSegment"]):
    def get_message_type(self):
        from nonebot.adapters.feishu.message import Message

        return Message

    @classmethod
    def get_adapter(cls) -> str:
        return "Feishu"

    def get_message_id(self, event: Event) -> str:
        from nonebot.adapters.feishu.event import MessageEvent

        assert isinstance(event, MessageEvent)
        return str(event.message_id)

    def get_target(self, event: Event) -> Target:
        from nonebot.adapters.feishu.event import GroupMessageEvent, PrivateMessageEvent

        if isinstance(event, GroupMessageEvent):
            return Target(event.event.message.chat_id)
        elif isinstance(event, PrivateMessageEvent):
            return Target(event.get_user_id(), private=True)
        raise NotImplementedError

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

        return ms("$reply", {"message_id": seg.id})  # type: ignore

    async def send_to(self, target: Target, bot: Bot, message: Message):
        from nonebot.adapters.feishu.bot import Bot as FeishuBot

        assert isinstance(bot, FeishuBot)
        if TYPE_CHECKING:
            assert isinstance(message, self.get_message_type())

        if target.private:
            receive_id, receive_id_type = target.id, "open_id"
        else:
            receive_id, receive_id_type = target.id, "chat_id"
        if message.has("$reply"):
            reply = message["$reply", 0]
            message = message.exclude("$reply")
            msg_type, content = message.serialize()
            return await bot.reply_msg(reply.data["message_id"], content, msg_type)
        msg_type, content = message.serialize()
        return await bot.send_msg(receive_id_type, receive_id, content, msg_type)

    async def recall(self, mid: Any, bot: Bot, context: Union[Target, Event]):
        from nonebot.adapters.feishu.bot import Bot as FeishuBot

        assert isinstance(bot, FeishuBot)

        params = {"method": "DELETE"}
        return await bot.call_api(f"im/v1/messages/{mid['message_id']}", **params)

    async def edit(self, new: Message, mid: Any, bot: Bot, context: Union[Target, Event]):
        from nonebot.adapters.feishu.bot import Bot as FeishuBot

        assert isinstance(bot, FeishuBot)
        if TYPE_CHECKING:
            assert isinstance(new, self.get_message_type())

        msg_type, content = new.serialize()
        params = {
            "method": "PUT",
            "body": {
                "content": content,
                "msg_type": msg_type,
            },
        }

        return await bot.call_api(f"im/v1/messages/{mid['message_id']}", **params)
