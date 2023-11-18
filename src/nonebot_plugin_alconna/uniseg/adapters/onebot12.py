from pathlib import Path
from typing import TYPE_CHECKING, Any, Union

from tarina import lang
from nonebot.adapters import Bot, Event, Message

from ..export import Target, MessageExporter, SerializeFailed, export
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

    def get_target(self, event: Event) -> Target:
        if channel_id := getattr(event, "channel_id", None):
            guild_id = getattr(event, "guild_id", None)
            return Target(str(channel_id), str(guild_id) if guild_id else "", channel=True)
        if guild_id := getattr(event, "guild_id", None):
            return Target(str(guild_id), channel=True)
        if group_id := getattr(event, "group_id", None):
            return Target(str(group_id))
        if user_id := getattr(event, "user_id", None):
            return Target(str(user_id), private=True)
        raise NotImplementedError

    def get_message_id(self, event: Event) -> str:
        from nonebot.adapters.onebot.v12.event import MessageEvent

        assert isinstance(event, MessageEvent)
        return str(event.message_id)

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
    async def media(self, seg: Union[Image, Voice, Video, Audio, File], bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        name = seg.__class__.__name__.lower()
        method = {
            "image": ms.image,
            "voice": ms.voice,
            "video": ms.video,
            "audio": ms.audio,
            "file": ms.file,
        }[name]
        if seg.id:
            return method(seg.id)
        elif seg.url:
            resp = await bot.upload_file(type="url", name=seg.name, url=seg.url)
            return method(resp["file_id"])
        elif seg.path:
            resp = await bot.upload_file(type="path", path=str(seg.path), name=Path(seg.path).name)
            return method(resp["file_id"])
        elif seg.raw:
            resp = await bot.upload_file(type="data", data=seg.raw_bytes, name=seg.name)
            return method(resp["file_id"])
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type=name, seg=seg))

    @export
    async def reply(self, seg: Reply, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.reply(seg.id)

    async def send_to(self, target: Target, bot: Bot, message: Message):
        from nonebot.adapters.onebot.v12.bot import Bot as OnebotBot

        assert isinstance(bot, OnebotBot)
        if TYPE_CHECKING:
            assert isinstance(message, self.get_message_type())

        if target.private:
            return await bot.send_message(detail_type="private", user_id=target.id, message=message)
        elif target.channel:
            return await bot.send_message(
                detail_type="channel", channel_id=target.id, guild_id=target.parent_id, message=message
            )
        else:
            return await bot.send_message(detail_type="group", group_id=target.id, message=message)

    async def recall(self, mid: Any, bot: Bot, context: Union[Target, Event]):
        from nonebot.adapters.onebot.v12.bot import Bot as OnebotBot

        assert isinstance(bot, OnebotBot)

        await bot.delete_message(message_id=mid["message_id"])
        return
