from pathlib import Path
from typing import TYPE_CHECKING, Union

from tarina import lang
from nonebot.adapters import Bot, Event
from nonebot.adapters.efchat.bot import Bot as EFBot
from nonebot.adapters.efchat.message import Message, MessageSegment
from nonebot.adapters.efchat.event import MessageEvent, ChannelMessageEvent

from nonebot_plugin_alconna.uniseg.constraint import SupportScope
from nonebot_plugin_alconna.uniseg.segment import At, Text, Audio, Image, Reply, Voice
from nonebot_plugin_alconna.uniseg.exporter import Target, SupportAdapter, MessageExporter, SerializeFailed, export


class EFChatMessageExporter(MessageExporter["Message"]):
    def get_message_type(self):
        return Message

    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.efchat

    def get_target(self, event: Event, bot: Union[Bot, None] = None) -> Target:
        if isinstance(event, ChannelMessageEvent):
            return Target(
                id=event.channel,
                self_id=bot.self_id if bot else None,
                scope=SupportScope.efchat,
                adapter=self.get_adapter(),
            )
        if nick := getattr(event, "nick", None):
            return Target(
                id=nick,
                private=True,
                self_id=bot.self_id if bot else None,
                scope=SupportScope.efchat,
                adapter=self.get_adapter(),
            )
        raise NotImplementedError

    def get_message_id(self, event: Event) -> str:
        assert isinstance(event, MessageEvent)
        return f"> {event.trip} {event.nick}:\n> {event.get_message()}\n\n"

    @export
    async def text(self, seg: Text, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.text(seg.text)

    @export
    async def at(self, seg: At, bot: Union[Bot, None]) -> "MessageSegment":
        if seg.flag != "user":
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="at", seg=seg))
        return MessageSegment.at(seg.target)

    @export
    async def image(self, seg: Image, bot: Union[Bot, None]) -> "MessageSegment":
        if seg.url:
            return MessageSegment.image(url=seg.url)
        if seg.__class__.to_url and seg.raw:
            return MessageSegment.image(
                await seg.__class__.to_url(seg.raw, bot, None if seg.name == seg.__default_name__ else seg.name)
            )
        if seg.__class__.to_url and seg.path:
            return MessageSegment.image(
                await seg.__class__.to_url(seg.path, bot, None if seg.name == seg.__default_name__ else seg.name)
            )
        raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="image", seg=seg))

    @export
    async def voice(self, seg: Union[Voice, Audio], bot: Union[Bot, None]) -> "MessageSegment":
        if seg.url:
            return MessageSegment.voice(url=seg.url)
        if seg.path:
            return MessageSegment.voice(path=Path(seg.path))
        if seg.raw:
            return MessageSegment.voice(raw=seg.raw_bytes)
        if seg.id:
            return MessageSegment.voice(src_name=seg.id)
        raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="voice", seg=seg))

    @export
    async def reply(self, seg: Reply, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.text(seg.id)

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: Message, **kwargs):
        assert isinstance(bot, EFBot)
        if TYPE_CHECKING:
            assert isinstance(message, self.get_message_type())

        if isinstance(target, MessageEvent):
            return await bot.send(target, message, **kwargs)
        if isinstance(target, Event):
            raise NotImplementedError
        if target.private:
            await bot.call_api("whisper", nick=target.id, text=str(message))
        await bot.move(target.id)
        await bot.send_chat_message(message=message, **kwargs)
