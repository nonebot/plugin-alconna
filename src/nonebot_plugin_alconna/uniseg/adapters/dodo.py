from pathlib import Path
from typing import TYPE_CHECKING, Any, Union, cast

from tarina import lang
from nonebot.drivers import Request
from nonebot.adapters import Bot, Event, Message

from ..segment import At, Text, Image, Reply, Video
from ..export import Target, MessageExporter, SerializeFailed, export

if TYPE_CHECKING:
    from nonebot.adapters.dodo.message import MessageSegment


class DoDoMessageExporter(MessageExporter["MessageSegment"]):
    @classmethod
    def get_adapter(cls) -> str:
        return "DoDo"

    def get_message_type(self):
        from nonebot.adapters.dodo.message import Message

        return Message

    def get_target(self, event: Event) -> Target:
        from nonebot.adapters.dodo.event import Event as DoDoEvent

        assert isinstance(event, DoDoEvent)
        channel_id = getattr(event, "channel_id", None)
        island_id = getattr(event, "island_source_id", None)
        if channel_id:
            return Target(channel_id, island_id or "", True)
        else:
            return Target(event.user_id, island_id or "", True, True)

    def get_message_id(self, event: Event) -> str:
        from nonebot.adapters.dodo.event import MessageEvent

        assert isinstance(event, MessageEvent)
        return event.message_id

    @export
    async def text(self, seg: Text, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.text(seg.text)

    @export
    async def at(self, seg: At, bot: Bot) -> "MessageSegment":
        ms = self.segment_class
        if seg.flag == "user":
            return ms.at_user(seg.target)
        elif seg.flag == "channel":
            return ms.channel_link(seg.target)
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="at", seg=seg))

    @export
    async def image(self, seg: Image, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        if TYPE_CHECKING:
            from nonebot.adapters.dodo.bot import Bot as DoDoBot

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

        return ms.picture(res.url, res.width, res.height)

    @export
    async def video(self, seg: Video, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        if seg.url:
            return ms.video(seg.url)
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="video", seg=seg))

    @export
    async def reply(self, seg: Reply, bot: Bot) -> "MessageSegment":
        ms = self.segment_class
        return ms.reference(seg.id)

    async def send_to(self, target: Target, bot: Bot, message: Message):
        from nonebot.adapters.dodo.bot import Bot as DodoBot

        assert isinstance(bot, DodoBot)
        if TYPE_CHECKING:
            assert isinstance(message, self.get_message_type())

        if target.private:
            return await bot.send_to_personal(target.parent_id, target.id, message)
        else:
            return await bot.send_to_channel(target.id, message)

    async def recall(self, mid: Any, bot: Bot, context: Union[Target, Event]):
        from nonebot.adapters.dodo.bot import Bot as DodoBot

        assert isinstance(bot, DodoBot)
        if isinstance(context, Target) and not context.private:
            return await bot.set_channel_message_withdraw(message_id=mid)
        elif hasattr(context, "channel_id"):
            return await bot.set_channel_message_withdraw(message_id=mid)

    async def edit(self, new: Message, mid: Any, bot: Bot, context: Union[Target, Event]):
        from nonebot.adapters.dodo.bot import Bot as DodoBot

        assert isinstance(bot, DodoBot)
        if TYPE_CHECKING:
            assert isinstance(new, self.get_message_type())
        if isinstance(context, Target) and not context.private:
            return await bot.set_channel_message_edit(message_id=mid, message_body=new.to_message_body()[0])
        elif hasattr(context, "channel_id"):
            return await bot.set_channel_message_edit(message_id=mid, message_body=new.to_message_body()[0])
