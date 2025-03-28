import asyncio
from typing import TYPE_CHECKING, Union

from tarina import lang
from nonebot.adapters import Bot, Event
from nonebot.adapters.gewechat.bot import Bot as GeWeChatBot
from nonebot.adapters.gewechat.event import (
    PokeEvent,
    NoticeEvent,
    RevokeEvent,
    MessageEvent,
    RequestEvent,
    FriendRemovedEvent,
    FriendInfoChangeEvent,
)

from nonebot_plugin_alconna.uniseg.constraint import SupportScope
from nonebot_plugin_alconna.uniseg.segment import At, File, Text, AtAll, Audio, Hyper, Image, Video, Voice
from nonebot_plugin_alconna.uniseg.exporter import Target, SupportAdapter, MessageExporter, SerializeFailed, export

if TYPE_CHECKING:
    from nonebot.adapters.gewechat.message import Message, MessageSegment


class GeWeChatMessageExporter(MessageExporter["Message"]):
    def get_message_type(self):
        from nonebot.adapters.gewechat.message import Message

        return Message

    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.gewechat

    def get_target(self, event: Event, bot: Union[Bot, None] = None) -> Target:
        if isinstance(event, MessageEvent):
            return Target(
                event.FromUserName,
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.wechat,
            )
        if isinstance(event, NoticeEvent):
            if isinstance(event, (FriendInfoChangeEvent, FriendRemovedEvent)):
                return Target(
                    event.FromUserName,
                    private=True,
                    adapter=self.get_adapter(),
                    self_id=bot.self_id if bot else None,
                    scope=SupportScope.wechat,
                )
            if isinstance(event, (PokeEvent, RevokeEvent)):
                return Target(
                    event.FromUserName,
                    private=event.FromUserName == getattr(event, "UserId", None),  # TODO: ensure RevokeEvent has UserId
                    adapter=self.get_adapter(),
                    self_id=bot.self_id if bot else None,
                    scope=SupportScope.wechat,
                )
            return Target(
                event.FromUserName,
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.wechat,
            )
        if isinstance(event, RequestEvent):
            return Target(
                event.FromUserName,
                private=True,
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.wechat,
            )
        raise NotImplementedError

    def get_message_id(self, event: Event) -> str:
        assert isinstance(event, MessageEvent)
        return str(event.MsgId)  # type: ignore

    @export
    async def text(self, seg: Text, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.text(seg.text)

    @export
    async def at(self, seg: At, bot: Union[Bot, None]) -> "MessageSegment":
        if seg.flag == "user":
            return MessageSegment.at(seg.target)
        raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="at", seg=seg))

    @export
    async def at_all(self, seg: AtAll, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.at_all()

    @export
    async def image(self, seg: Image, bot: Union[Bot, None]) -> "MessageSegment":
        if seg.url:
            return MessageSegment.image(seg.url)
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
            return MessageSegment.voice(seg.url, int(seg.duration or 1.0))
        if seg.__class__.to_url and seg.raw:
            return MessageSegment.voice(
                await seg.__class__.to_url(seg.raw, bot, None if seg.name == seg.__default_name__ else seg.name),
                int(seg.duration or 1.0),
            )
        if seg.__class__.to_url and seg.path:
            return MessageSegment.voice(
                await seg.__class__.to_url(seg.path, bot, None if seg.name == seg.__default_name__ else seg.name),
                int(seg.duration or 1.0),
            )
        raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="voice", seg=seg))

    @export
    async def file(self, seg: File, bot: Union[Bot, None]) -> "MessageSegment":
        if seg.url:
            return MessageSegment.file(seg.url, seg.name)
        if seg.__class__.to_url and seg.raw:
            return MessageSegment.file(
                await seg.__class__.to_url(seg.raw, bot, None if seg.name == seg.__default_name__ else seg.name),
                seg.name,
            )
        if seg.__class__.to_url and seg.path:
            return MessageSegment.file(
                await seg.__class__.to_url(seg.path, bot, None if seg.name == seg.__default_name__ else seg.name),
                seg.name,
            )
        raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="file", seg=seg))

    @export
    async def video(self, seg: Video, bot: Union[Bot, None]) -> "MessageSegment":
        if not seg.thumbnail:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="video", seg=seg))
        if seg.thumbnail.url:
            thumbUrl = seg.thumbnail.url
        elif seg.__class__.to_url and seg.thumbnail.raw:
            thumbUrl = await seg.__class__.to_url(
                seg.thumbnail.raw,
                bot,
                None if seg.thumbnail.name == seg.thumbnail.__default_name__ else seg.thumbnail.name,
            )
        elif seg.__class__.to_url and seg.thumbnail.path:
            thumbUrl = await seg.__class__.to_url(
                seg.thumbnail.path,
                bot,
                None if seg.thumbnail.name == seg.thumbnail.__default_name__ else seg.thumbnail.name,
            )
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="video", seg=seg))
        if seg.url:
            return MessageSegment.video(seg.url, thumbUrl, int(seg.duration or 1.0))
        if seg.__class__.to_url and seg.raw:
            return MessageSegment.video(
                await seg.__class__.to_url(seg.raw, bot, None if seg.name == seg.__default_name__ else seg.name),
                thumbUrl,
                int(seg.duration or 1.0),
            )
        if seg.__class__.to_url and seg.path:
            return MessageSegment.video(
                await seg.__class__.to_url(seg.path, bot, None if seg.name == seg.__default_name__ else seg.name),
                thumbUrl,
                int(seg.duration or 1.0),
            )
        raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="video", seg=seg))

    @export
    async def hyper(self, seg: Hyper, bot: Union[Bot, None]) -> "MessageSegment":
        if seg.format == "json" and isinstance(data := seg.content, dict):
            if "nameCardWxid" in data:
                return MessageSegment.namecard(**data)
            if "miniAppId" in data:
                return MessageSegment.miniapp(**data)
            if "linkUrl" in data:
                return MessageSegment.link(**data)
        if seg.format != "xml" or not seg.raw:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="hyper", seg=seg))
        return MessageSegment.xml(seg.raw)

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: "Message", **kwargs):
        assert isinstance(bot, GeWeChatBot)

        if isinstance(target, Event):
            return await bot.send(target, message, **kwargs)  # type: ignore

        to_wxid = target.id
        tasks = []
        for api, data in message.to_payload():
            data["toWxid"] = to_wxid
            data["appId"] = bot.adapter.adapter_config.appid

            tasks.append(bot.call_api(api, **data))

        return await asyncio.gather(*tasks)
