from pathlib import Path
from typing import Any, Sequence

from nonebot.adapters import Bot, Event
from nonebot.adapters.vocechat.bot import Bot as VcBot
from nonebot.adapters.vocechat.event import GroupMessageEvent, MessageEvent
from nonebot.adapters.vocechat.message import Message, MessageSegment
from tarina import lang

from nonebot_plugin_alconna.uniseg.constraint import SupportScope
from nonebot_plugin_alconna.uniseg.exporter import MessageExporter, SerializeFailed, SupportAdapter, Target, export
from nonebot_plugin_alconna.uniseg.segment import At, Audio, File, Image, Reply, Segment, Text, Video, Voice


class VocechatMessageExporter(MessageExporter[Message]):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.vocechat

    def get_message_type(self):
        return Message

    def get_target(self, event: Event, bot: Bot | None = None) -> Target:
        assert isinstance(event, MessageEvent)
        if isinstance(event, GroupMessageEvent) or event.target.gid is not None:
            return Target(
                str(event.target.gid),
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.vocechat,
            )
        return Target(
            str(event.target.uid or event.from_uid),
            private=True,
            adapter=self.get_adapter(),
            self_id=bot.self_id if bot else None,
            scope=SupportScope.vocechat,
        )

    def get_message_id(self, event: Event) -> str:
        assert isinstance(event, MessageEvent)
        return str(event.message_id or event.mid)

    @export
    async def text(self, seg: Text, bot: Bot | None) -> MessageSegment:
        if seg.extract_most_style() == "markdown":
            return MessageSegment.markdown(seg.text)
        return MessageSegment.text(seg.text)

    @export
    async def at(self, seg: At, bot: Bot | None) -> MessageSegment:
        if seg.flag != "user":
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="at", seg=seg))
        return MessageSegment.mention(int(seg.target))

    def _media_properties(self, seg: Image | Voice | Video | Audio | File) -> dict[str, Any] | None:
        properties: dict[str, Any] = {}
        if isinstance(seg, Image):
            if seg.width is not None:
                properties["width"] = seg.width
            if seg.height is not None:
                properties["height"] = seg.height
        if isinstance(seg, (Audio, Voice, Video)) and seg.duration is not None:
            properties["duration"] = seg.duration
        return properties or None

    async def _media(self, seg: Image | Voice | Video | Audio | File, name: str) -> MessageSegment:
        method = {
            "image": MessageSegment.image,
            "voice": MessageSegment.audio,
            "audio": MessageSegment.audio,
            "video": MessageSegment.video,
            "file": MessageSegment.file,
        }[name]
        filename = None if seg.name == seg.__default_name__ else seg.name
        properties = self._media_properties(seg)
        if seg.id:
            return method(file_id=seg.id, filename=filename, properties=properties)
        if seg.path:
            return method(file=Path(seg.path), filename=filename, properties=properties)
        if seg.raw:
            return method(file=seg.raw_bytes, filename=filename, properties=properties)
        raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type=name, seg=seg))

    @export
    async def media(self, seg: Image | Voice | Video | Audio | File, bot: Bot | None) -> MessageSegment:
        return await self._media(seg, seg.__class__.__name__.lower())

    def _pop_reply(self, message: Message) -> tuple[int | None, Message]:
        reply_id: int | None = None
        new_message = self.get_message_type()([])
        for seg in message:
            if seg.type == "$vocechat:reply":
                if reply_id is None:
                    reply_id = int(seg.data["mid"])
                continue
            new_message.append(seg)
        return reply_id, new_message

    @export
    async def reply(self, seg: Reply, bot: Bot | None) -> MessageSegment:
        return MessageSegment("$vocechat:reply", {"mid": int(seg.id)})

    async def send_to(self, target: Target | Event, bot: Bot, message: Message, **kwargs):
        assert isinstance(bot, VcBot)
        reply_id, message = self._pop_reply(message)
        if isinstance(target, MessageEvent):
            if reply_id is not None:
                return await bot.send_message(message=message, reply=reply_id, **kwargs)
            return await bot.send(target, message, **kwargs)
        if isinstance(target, Event):
            raise NotImplementedError
        if reply_id is not None:
            return await bot.send_message(message=message, reply=reply_id, **kwargs)
        if target.private:
            return await bot.send_message(message=message, user_id=int(target.id), **kwargs)
        return await bot.send_message(message=message, group_id=int(target.id), **kwargs)

    async def recall(self, mid: Any, bot: Bot, context: Target | Event):
        assert isinstance(bot, VcBot)
        if isinstance(mid, str):
            return await bot.delete(int(mid))
        return await bot.delete(int(mid))

    async def edit(self, new: Sequence[Segment], mid: Any, bot: Bot, context: Target | Event):
        assert isinstance(bot, VcBot)
        new_msg = await self.export(new, bot, True)
        _, new_msg = self._pop_reply(new_msg)
        return await bot.edit(int(mid), new_msg)

    def get_reply(self, mid: Any):
        return Reply(str(mid))
