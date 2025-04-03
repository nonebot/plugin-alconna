from pathlib import Path
from typing import TYPE_CHECKING, Any, Union, Sequence, cast

from tarina import lang
from nonebot.drivers import Request
from nonebot.adapters import Bot, Event
from nonebot.adapters.dodo.bot import Bot as DoDoBot
from nonebot.adapters.dodo.event import MessageEvent
from nonebot.adapters.dodo.event import Event as DoDoEvent
from nonebot.adapters.dodo.models import Emoji as DodoEmoji
from nonebot.adapters.dodo.message import Message, MessageSegment

from nonebot_plugin_alconna.uniseg.constraint import SupportScope
from nonebot_plugin_alconna.uniseg.segment import At, Text, Emoji, Image, Reply, Video, Segment
from nonebot_plugin_alconna.uniseg.exporter import Target, SupportAdapter, MessageExporter, SerializeFailed, export


class DoDoMessageExporter(MessageExporter[Message]):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.dodo

    def get_message_type(self):
        return Message

    def get_target(self, event: Event, bot: Union[Bot, None] = None) -> Target:
        event = cast(DoDoEvent, event)
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
        return Target(
            event.get_user_id(),
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
    async def text(self, seg: Text, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.text(seg.text)

    @export
    async def at(self, seg: At, bot: Union[Bot, None]) -> "MessageSegment":
        if seg.flag == "user":
            return MessageSegment.at_user(seg.target)
        if seg.flag == "channel":
            return MessageSegment.channel_link(seg.target)
        raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="at", seg=seg))

    @export
    async def image(self, seg: Image, bot: Union[Bot, None]) -> "MessageSegment":
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
    async def video(self, seg: Video, bot: Union[Bot, None]) -> "MessageSegment":
        if seg.url:
            return MessageSegment.video(seg.url)
        raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="video", seg=seg))

    @export
    async def reply(self, seg: Reply, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.reference(seg.id)

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: Message, **kwargs):
        assert isinstance(bot, DoDoBot)
        if TYPE_CHECKING:
            assert isinstance(message, Message)

        if isinstance(target, Event):
            return await bot.send(target, message, **kwargs)  # type: ignore

        if target.private:
            return await bot.send_to_personal(target.parent_id, target.id, message)
        return await bot.send_to_channel(target.id, message)

    async def recall(self, mid: Any, bot: Bot, context: Union[Target, Event]):
        assert isinstance(bot, DoDoBot)
        if isinstance(context, Target) and not context.private:
            return await bot.set_channel_message_withdraw(message_id=mid)
        if hasattr(context, "channel_id"):
            return await bot.set_channel_message_withdraw(message_id=mid)
        return None

    async def edit(self, new: Sequence[Segment], mid: Any, bot: Bot, context: Union[Target, Event]):
        assert isinstance(bot, DoDoBot)
        new_msg = await self.export(new, bot, True)
        if isinstance(context, Target) and not context.private:
            return await bot.set_channel_message_edit(message_id=mid, message_body=new_msg.to_message_body()[0])
        if hasattr(context, "channel_id"):
            return await bot.set_channel_message_edit(message_id=mid, message_body=new_msg.to_message_body()[0])
        return None

    async def reaction(self, emoji: Emoji, mid: Any, bot: Bot, context: Union[Target, Event], delete: bool = False):
        assert isinstance(bot, DoDoBot)
        emj = DodoEmoji(type=1, id=emoji.id)
        if delete:
            await bot.set_channel_message_reaction_remove(message_id=mid, emoji=emj)
        else:
            await bot.set_channel_message_reaction_add(message_id=mid, emoji=emj)

    def get_reply(self, mid: Any):
        return Reply(mid)
