from typing import Union

from tarina import lang
from nonebot.adapters import Bot, Event
from nonebot.adapters.ntchat.bot import send
from nonebot.adapters.ntchat.event import MessageEvent
from nonebot.adapters.ntchat.bot import Bot as NTChatBot
from nonebot.adapters.ntchat.message import Message, MessageSegment

from nonebot_plugin_alconna.uniseg.constraint import SupportScope
from nonebot_plugin_alconna.uniseg.segment import File, Text, Hyper, Image, Video
from nonebot_plugin_alconna.uniseg.exporter import Target, SupportAdapter, MessageExporter, SerializeFailed, export


class NTChatMessageExporter(MessageExporter[Message]):
    def get_message_type(self):
        return Message

    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.ntchat

    def get_target(self, event: Event, bot: Union[Bot, None] = None) -> Target:
        from_wxid = getattr(event, "from_wxid", None)
        room_wxid = getattr(event, "room_wxid", "")
        if from_wxid:
            return Target(
                from_wxid,
                room_wxid,
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.wechat,
            )
        raise NotImplementedError

    def get_message_id(self, event: Event) -> str:
        assert isinstance(event, MessageEvent)
        return str(event.msgid)

    @export
    async def text(self, seg: Text, bot: Bot) -> "MessageSegment":
        return MessageSegment.text(seg.text)

    @export
    async def res(self, seg: Union[Image, File, Video], bot: Bot) -> "MessageSegment":
        name = seg.__class__.__name__.lower()
        method = {
            "image": MessageSegment.image,
            "video": MessageSegment.video,
            "file": MessageSegment.file,
        }[name]
        if seg.path:
            return method(seg.path)
        elif seg.raw:
            return method(seg.raw_bytes)
        elif seg.url or seg.id:
            return method(seg.url or seg.id)  # type: ignore
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type=name, seg=seg))

    @export
    async def hyper(self, seg: Hyper, bot: Bot) -> "MessageSegment":
        if seg.format == "json" and seg.content and "card_wxid" in seg.content:
            return MessageSegment.card(seg.content["card_wxid"])  # type: ignore
        if seg.format != "xml" or not seg.raw:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="hyper", seg=seg))
        return MessageSegment.xml(seg.raw)

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: Message):
        assert isinstance(bot, NTChatBot)

        if isinstance(target, Event):
            target = self.get_target(target, bot)

        class FakeEvent:
            from_wxid = target.id
            if target.parent_id:
                room_wxid = target.parent_id

        return await send(bot, FakeEvent, message)  # type: ignore
