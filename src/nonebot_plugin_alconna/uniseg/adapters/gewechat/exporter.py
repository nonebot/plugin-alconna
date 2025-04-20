import asyncio
from pathlib import Path
from typing import Any, Union, cast

from tarina import lang
from nonebot.adapters import Bot, Event
from nonebot.compat import type_validate_python
from nonebot.adapters.gewechat.utils import resp_json
from nonebot.adapters.gewechat.bot import Bot as GeWeChatBot
from nonebot.adapters.gewechat.api_model import postMessageResponse
from nonebot.adapters.gewechat.message import Message, MessageSegment
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
from nonebot_plugin_alconna.uniseg.exporter import Target, SupportAdapter, MessageExporter, SerializeFailed, export
from nonebot_plugin_alconna.uniseg.segment import At, File, Text, AtAll, Audio, Emoji, Hyper, Image, Reply, Video, Voice


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
    async def emoji(self, seg: Emoji, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.emoji(seg.id, len(seg.id))

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
                Path(seg.path).name if seg.name == seg.__default_name__ else seg.name,
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

    @export
    async def reply(self, seg: Reply, bot: Union[Bot, None]):
        if not bot:
            return []
        assert isinstance(bot, GeWeChatBot)
        if not (origin_event := bot.getMessageEventByMsgId(seg.id)):
            return []
        return MessageSegment.quote(origin_event.FromUserName, origin_event.ToUserName, seg.id)

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: "Message", **kwargs):
        assert isinstance(bot, GeWeChatBot)

        if isinstance(target, Event):
            resps = await bot.send(target, message, **kwargs)  # type: ignore
        else:
            to_wxid = target.id
            tasks = []
            for api, data in message.to_payload():
                data["toWxid"] = to_wxid
                data["appId"] = bot.adapter.adapter_config.appid

                tasks.append(bot.call_api(api, **data))

            resps = [
                type_validate_python(postMessageResponse, resp_json(resp)) for resp in await asyncio.gather(*tasks)
            ]
        return resps

    async def recall(self, mid: Any, bot: Bot, context: Union[Target, Event]):
        assert isinstance(bot, GeWeChatBot)
        if isinstance(mid, (str, int)) and isinstance(context, MessageEvent):
            await bot.revokeMsg(context.ToUserName, str(context.MsgId), str(context.NewMsgId), str(context.CreateTime))
        else:
            mid = cast(postMessageResponse, mid)
            resp = mid.data
            await bot.revokeMsg(resp.toWxid, str(resp.msgId), str(resp.newMsgId), str(resp.createTime))
