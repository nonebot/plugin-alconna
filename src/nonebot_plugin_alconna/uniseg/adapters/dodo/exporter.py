from pathlib import Path
from typing import TYPE_CHECKING, Any, Union, cast

from tarina import lang
from nonebot.drivers import Request
from nonebot.adapters import Bot, Event
from nonebot.adapters.dodo.bot import Bot as DoDoBot
from nonebot.adapters.dodo.event import MessageEvent
from nonebot.adapters.dodo.event import Event as DoDoEvent
from nonebot.adapters.dodo.message import Message, MessageSegment

from nonebot_plugin_alconna.uniseg.constraint import SupportScope
from nonebot_plugin_alconna.uniseg.segment import At, Text, Image, Reply, Video
from nonebot_plugin_alconna.uniseg.exporter import Target, SupportAdapter, MessageExporter, SerializeFailed, export


class DoDoMessageExporter(MessageExporter[Message]):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.dodo

    def get_message_type(self):
        return Message

    def get_target(self, event: Event, bot: Union[Bot, None] = None) -> Target:
        assert isinstance(event, DoDoEvent)
        channel_id = getattr(event, "channel_id", None)
        island_id = getattr(event, "island_source_id", None)
        if channel_id:
            return Target(
                channel_id,
                island_id or "",
                True,
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.dodo,
            )
        else:
            return Target(
                event.user_id,
                island_id or "",
                True,
                True,
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.dodo,
            )

    def get_message_id(self, event: Event) -> str:
        assert isinstance(event, MessageEvent)
        return event.message_id

    @export
    async def text(self, seg: Text, bot: Bot) -> "MessageSegment":
        return MessageSegment.text(seg.text)

    @export
    async def at(self, seg: At, bot: Bot) -> "MessageSegment":
        if seg.flag == "user":
            return MessageSegment.at_user(seg.target)
        elif seg.flag == "channel":
            return MessageSegment.channel_link(seg.target)
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="at", seg=seg))

    @export
    async def image(self, seg: Image, bot: Bot) -> "MessageSegment":
        if TYPE_CHECKING:
            assert isinstance(bot, DoDoBot)
        if seg.raw:
            data = seg.raw_bytes
        elif seg.path:
            data = Path(seg.path)
        elif seg.url:
            resp = await bot.adapter.request(Request("GET", seg.url))
            data = cast(bytes, resp.content)
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="image", seg=seg))
        res = await bot.set_resouce_picture_upload(file=data)

        return MessageSegment.picture(res.url, res.width, res.height)

    @export
    async def video(self, seg: Video, bot: Bot) -> "MessageSegment":
        if seg.url:
            return MessageSegment.video(seg.url)
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="video", seg=seg))

    @export
    async def reply(self, seg: Reply, bot: Bot) -> "MessageSegment":
        return MessageSegment.reference(seg.id)

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: Message):
        assert isinstance(bot, DoDoBot)
        if TYPE_CHECKING:
            assert isinstance(message, Message)

        if isinstance(target, Event):
            target = self.get_target(target, bot)

        if target.private:
            return await bot.send_to_personal(target.parent_id, target.id, message)
        else:
            return await bot.send_to_channel(target.id, message)

    async def recall(self, mid: Any, bot: Bot, context: Union[Target, Event]):
        assert isinstance(bot, DoDoBot)
        if isinstance(context, Target) and not context.private:
            return await bot.set_channel_message_withdraw(message_id=mid)
        elif hasattr(context, "channel_id"):
            return await bot.set_channel_message_withdraw(message_id=mid)

    async def edit(self, new: Message, mid: Any, bot: Bot, context: Union[Target, Event]):
        assert isinstance(bot, DoDoBot)
        if TYPE_CHECKING:
            assert isinstance(new, Message)
        if isinstance(context, Target) and not context.private:
            return await bot.set_channel_message_edit(message_id=mid, message_body=new.to_message_body()[0])
        elif hasattr(context, "channel_id"):
            return await bot.set_channel_message_edit(message_id=mid, message_body=new.to_message_body()[0])

    def get_reply(self, mid: Any):
        return Reply(mid)
