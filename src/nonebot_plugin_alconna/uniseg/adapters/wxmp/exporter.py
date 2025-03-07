from pathlib import Path
from typing import Union

from tarina import lang
from nonebot.adapters import Bot, Event
from nonebot.adapters.wxmp import Bot as WXMPBot
from nonebot.adapters.wxmp.event import MessageEvent
from nonebot.adapters.wxmp.event import Event as WXMPEvent
from nonebot.adapters.wxmp.message import Message, EmjoyType, MessageSegment

from nonebot_plugin_alconna.uniseg.constraint import SupportScope, SerializeFailed
from nonebot_plugin_alconna.uniseg.segment import Text, Audio, Emoji, Hyper, Image, Video, Voice
from nonebot_plugin_alconna.uniseg.exporter import Target, SupportAdapter, MessageExporter, export


class WXMPMessageExporter(MessageExporter[Message]):
    def get_message_type(self):
        return Message

    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.wxmp

    def get_target(self, event: Event, bot: Union[Bot, None] = None) -> Target:
        assert isinstance(event, WXMPEvent)
        return Target(
            event.get_user_id(),
            private=True,
            adapter=self.get_adapter(),
            self_id=bot.self_id if bot else None,
            scope=SupportScope.wechat_oap,
        )

    def get_message_id(self, event: Event) -> str:
        assert isinstance(event, MessageEvent)
        return str(event.message_id)

    @export
    async def text(self, seg: Text, bot: Union[Bot, None]) -> "MessageSegment":
        if not seg.styles:
            return MessageSegment.text(seg.text)
        style = seg.extract_most_style()
        if style == "link":
            title = desc = url = seg.text
            if getattr(seg, "_children", []):
                title = desc = seg._children[0].text  # type: ignore
            return MessageSegment.link(title, desc, url)
        return MessageSegment.text(seg.text)

    @export
    async def media(self, seg: Union[Image, Voice, Video, Audio], bot: Union[Bot, None]) -> "MessageSegment":
        name = seg.__class__.__name__.lower()
        methods = {
            "image": MessageSegment.image,
            "voice": MessageSegment.voice,
            "video": MessageSegment.video,
            "audio": MessageSegment.voice,
        }
        if seg.id:
            return methods[name](media_id=seg.id)
        if seg.raw:
            if name in ("voice", "audio"):
                return MessageSegment.voice(file=seg.raw_bytes, format=seg.mimetype)
            return methods[name](file=seg.raw_bytes)
        if seg.path:
            return methods[name](file_path=Path(seg.path))
        if seg.url and name == "image":
            return MessageSegment.image(file_url=seg.url)  # type: ignore
        raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type=name, seg=seg))

    @export
    async def emoji(self, seg: Emoji, bot: Union[Bot, None]) -> "MessageSegment":
        t = EmjoyType(seg.name)
        return MessageSegment.emjoy(t)

    @export
    async def hyper(self, seg: Hyper, bot: Union[Bot, None]) -> "MessageSegment":
        if isinstance(seg.content, dict):
            return MessageSegment.miniprogrampage(**seg.content)
        raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="hyper", seg=seg))

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: Message, **kwargs):
        assert isinstance(bot, WXMPBot)

        if isinstance(target, Event):
            return await bot.send(target, message, **kwargs)  # type: ignore
        return await bot.send_custom_message(user_id=target.id, message=message)
