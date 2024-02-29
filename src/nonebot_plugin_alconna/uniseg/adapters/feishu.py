from pathlib import Path
from typing import TYPE_CHECKING, Any, Union

from tarina import lang
from nonebot.internal.driver import Request
from nonebot.adapters import Bot, Event, Message

from ..segment import At, File, Text, AtAll, Audio, Image, Reply, Video, Voice
from ..export import Target, SupportAdapter, MessageExporter, SerializeFailed, export

if TYPE_CHECKING:
    from nonebot.adapters.feishu.message import MessageSegment


class FeishuMessageExporter(MessageExporter["MessageSegment"]):
    def get_message_type(self):
        from nonebot.adapters.feishu.message import Message

        return Message

    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.feishu

    def get_message_id(self, event: Event) -> str:
        from nonebot.adapters.feishu.event import MessageEvent

        assert isinstance(event, MessageEvent)
        return str(event.message_id)

    def get_target(self, event: Event, bot: Union[Bot, None] = None) -> Target:
        from nonebot.adapters.feishu.event import GroupMessageEvent, PrivateMessageEvent

        if isinstance(event, GroupMessageEvent):
            return Target(
                event.event.message.chat_id, platform=self.get_adapter(), self_id=bot.self_id if bot else None
            )
        elif isinstance(event, PrivateMessageEvent):
            return Target(
                event.get_user_id(),
                private=True,
                platform=self.get_adapter(),
                self_id=bot.self_id if bot else None,
            )
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
        file_key = result["data"]["image_key"]
        return ms.image(file_key)

    @export
    async def audio(self, seg: Union[Voice, Audio], bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        name = seg.__class__.__name__.lower()
        if seg.id:
            return ms.audio(seg.id, seg.duration)
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
        file_key = result["data"]["file_key"]
        return ms.audio(file_key, seg.duration)

    @export
    async def file(self, seg: File, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        if seg.id:
            return ms.file(seg.id, seg.name)
        elif seg.url:
            resp = await bot.adapter.request(Request("GET", seg.url))
            raw = resp.content
        elif seg.path:
            raw = Path(seg.path).read_bytes()
        elif seg.raw:
            raw = seg.raw_bytes
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="file", seg=seg))
        data = {"file_type": "stream", "file_name": seg.name}
        files = {"file": ("file", raw)}
        params = {"method": "POST", "data": data, "files": files}
        result = await bot.call_api("im/v1/files", **params)
        file_key = result["data"]["file_key"]
        return ms.file(file_key, seg.name)

    @export
    async def video(self, seg: Video, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        if seg.id:
            return ms.sticker(seg.id)
        elif seg.url:
            resp = await bot.adapter.request(Request("GET", seg.url))
            raw = resp.content
        elif seg.path:
            raw = Path(seg.path).read_bytes()
        elif seg.raw:
            raw = seg.raw_bytes
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="video", seg=seg))
        data = {"file_type": "stream", "file_name": seg.name}
        files = {"file": ("file", raw)}
        params = {"method": "POST", "data": data, "files": files}
        result = await bot.call_api("im/v1/files", **params)
        file_key = result["data"]["file_key"]
        return ms.sticker(file_key)

    @export
    async def reply(self, seg: Reply, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms("$reply", {"message_id": seg.id})  # type: ignore

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: Message):
        from nonebot.adapters.feishu.bot import Bot as FeishuBot

        assert isinstance(bot, FeishuBot)
        if TYPE_CHECKING:
            assert isinstance(message, self.get_message_type())

        if isinstance(target, Event):
            target = self.get_target(target, bot)

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

    def get_reply(self, mid: Any):
        return Reply(mid["message_id"])
