from pathlib import Path
from typing import Union

from tarina import lang
from nonebot.adapters import Bot, Event
from nonebot.internal.driver import Request
from nonebot.adapters.mail import Bot as MailBot
from nonebot.adapters.mail.event import NewMailMessageEvent
from nonebot.adapters.mail.message import Message, MessageSegment

from nonebot_plugin_alconna.uniseg.constraint import SupportScope, SerializeFailed
from nonebot_plugin_alconna.uniseg.exporter import Target, SupportAdapter, MessageExporter, export
from nonebot_plugin_alconna.uniseg.segment import At, File, Text, Audio, Image, Reply, Video, Voice


class MailMessageExporter(MessageExporter[Message]):
    def get_message_type(self):
        return Message

    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.mail

    def get_target(self, event: Event, bot: Union[Bot, None] = None) -> Target:
        assert isinstance(event, NewMailMessageEvent)
        return Target(
            event.get_user_id(),
            private=True,
            adapter=self.get_adapter(),
            self_id=bot.self_id if bot else None,
            scope=SupportScope.mail,
        )

    def get_message_id(self, event: Event) -> str:
        assert isinstance(event, NewMailMessageEvent)
        return event.id

    @export
    async def text(self, seg: Text, bot: Union[Bot, None]) -> "MessageSegment":
        if not seg.styles:
            return MessageSegment.text(seg.text)
        style = seg.extract_most_style()
        if style == "link":
            if not getattr(seg, "_children", []):
                return MessageSegment.html(f'<a href="{seg.text}">{seg.text}</a>')
            return MessageSegment.html(f'<a href="{seg.text}">{seg._children[0].text}</a>')  # type: ignore
        return MessageSegment.html(str(seg))

    @export
    async def at(self, seg: At, bot: Union[Bot, None]) -> "MessageSegment":
        if seg.flag == "user":
            return MessageSegment.html(f'<a href="mailto:{seg.target}">@{seg.target}</a>')
        if seg.flag == "channel":
            return MessageSegment.html(f" #{seg.target}")
        raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="at", seg=seg))

    @export
    async def media(self, seg: Union[Image, Voice, Video, Audio, File], bot: Union[Bot, None]) -> "MessageSegment":
        name = seg.__class__.__name__.lower()

        if seg.raw and (seg.id or seg.name):
            return MessageSegment.attachment(seg.raw, seg.id or seg.name, seg.mimetype)
        if seg.path:
            path = Path(seg.path)
            return MessageSegment.attachment(path, path.name)
        if bot and seg.url:
            if name == "image":
                return MessageSegment.html(f'<img src="{seg.url}" />')
            if name == "video":
                return MessageSegment.html(f'<video src="{seg.url}" controls />')
            if name in ["audio", "voice"]:
                return MessageSegment.html(f'<audio src="{seg.url}" controls />')
            resp = await bot.adapter.request(Request("GET", seg.url))
            return MessageSegment.attachment(
                resp.content,  # type: ignore
                seg.id or seg.name or seg.url.split("/")[-1],
            )
        raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type=name, seg=seg))

    @export
    async def reply(self, seg: Reply, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment("mail:reply", {"message_id": seg.id})  # type: ignore

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: Message, **kwargs):
        assert isinstance(bot, MailBot)

        in_reply_to = None
        if message.has("$mail:reply"):
            reply = message["mail:reply", 0]
            message = message.exclude("mail:reply")
            in_reply_to = reply.data["message_id"]

        if isinstance(target, Event):
            return await bot.send(target, message, in_reply_to=in_reply_to, **kwargs)  # type: ignore
        return await bot.send_to(recipient=target.id, message=message, in_reply_to=in_reply_to, **kwargs)
