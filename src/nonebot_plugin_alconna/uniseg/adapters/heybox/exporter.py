from typing import TYPE_CHECKING, Union

from tarina import lang
from nonebot.adapters import Bot, Event
from nonebot.adapters.heybox.bot import Bot as HeyboxBot
from nonebot.adapters.heybox.event import UserIMMessageEvent
from nonebot.adapters.heybox.message import Message, MessageSegment

from nonebot_plugin_alconna.uniseg.constraint import SupportScope
from nonebot_plugin_alconna.uniseg.segment import At, Text, Image, Reply
from nonebot_plugin_alconna.uniseg.exporter import Target, SupportAdapter, MessageExporter, SerializeFailed, export


class HeyboxMessageExporter(MessageExporter[Message]):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.heybox

    def get_message_type(self):
        return Message

    def get_target(self, event: Event, bot: Union[Bot, None] = None) -> Target:
        if isinstance(event, UserIMMessageEvent):
            return Target(
                event.channel_id,
                parent_id=event.room_id,
                channel=True,
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.heybox,
            )
        raise NotImplementedError

    def get_message_id(self, event: Event) -> str:
        if isinstance(event, UserIMMessageEvent):
            return str(event.im_seq)
        raise NotImplementedError

    @export
    async def text(self, seg: Text, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.text(seg.text)

    @export
    async def at(self, seg: At, bot: Union[Bot, None]) -> "MessageSegment":
        if seg.flag == "user":
            return MessageSegment.mention(seg.target)
        raise SerializeFailed(
            lang.require("nbp-uniseg", "failed_segment").format(adapter="qq", seg=seg, target="mention")
        )

    @export
    async def image(self, seg: Image, bot: Union[Bot, None]) -> "MessageSegment":
        if seg.url:
            return MessageSegment.image(url=seg.url, width=seg.width or 0, height=seg.height or 0)
        if seg.raw:
            return MessageSegment.local_image(
                seg.raw_bytes, width=seg.width or 0, height=seg.height or 0, filename=seg.name
            )
        raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="image", seg=seg))

    @export
    async def reply(self, seg: Reply, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment("$heybox:reply", {"message_id": seg.id})  # type: ignore

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: Message, **kwargs):
        assert isinstance(bot, HeyboxBot)

        reply_id = None
        if message.has("$heybox:reply"):
            reply_id = message["$heybox:reply", 0].data["message_id"]
            message = message.exclude("$heybox:reply")

        if isinstance(target, Event):
            if TYPE_CHECKING:
                assert isinstance(target, UserIMMessageEvent)
            return await bot.send(event=target, message=message, **kwargs, is_reply=reply_id is not None)
        return await bot.send_to_channel(
            target.parent_id,
            target.id,
            message,
            reply_id=reply_id,
        )
