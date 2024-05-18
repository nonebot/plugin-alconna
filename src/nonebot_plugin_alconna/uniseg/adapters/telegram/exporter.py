from pathlib import Path
from typing import Any, Union, cast

from tarina import lang
from nonebot.adapters import Bot, Event
from nonebot.adapters.telegram.message import Entity
from nonebot.adapters.telegram.message import Message
from nonebot.adapters.telegram.bot import Bot as TgBot
from nonebot.adapters.telegram.event import Event as TgEvent
from nonebot.adapters.telegram.message import File as TgFile
from nonebot.adapters.telegram.message import MessageSegment
from nonebot.adapters.telegram.message import Reply as TgReply
from nonebot.adapters.telegram.message import Message as TgMessage
from nonebot.adapters.telegram.model import Message as MessageModel
from nonebot.adapters.telegram.event import MessageEvent, EventWithChat

from nonebot_plugin_alconna.uniseg.constraint import SupportScope
from nonebot_plugin_alconna.uniseg.segment import At, File, Text, Audio, Emoji, Image, Reply, Video, Voice
from nonebot_plugin_alconna.uniseg.exporter import Target, SupportAdapter, MessageExporter, SerializeFailed, export

STYLE_TYPE_MAP = {
    "b": "bold",
    "strong": "bold",
    "bold": "bold",
    "i": "italic",
    "em": "italic",
    "italic": "italic",
    "u": "underline",
    "ins": "underline",
    "underline": "underline",
    "s": "strikethrough",
    "del": "strikethrough",
    "strike": "strikethrough",
    "strikethrough": "strikethrough",
    "spl": "spoiler",
    "spoiler": "spoiler",
    "blockquote": "spoiler",
    "code": "code",
}


class TelegramMessageExporter(MessageExporter[Message]):
    def get_message_type(self):
        return Message

    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.telegram

    def get_target(self, event: Event, bot: Union[Bot, None] = None) -> Target:
        assert isinstance(event, EventWithChat)
        return Target(
            str(event.chat.id),
            private=event.chat.type == "private",
            adapter=self.get_adapter(),
            self_id=bot.self_id if bot else None,
            scope=SupportScope.telegram,
        )

    def get_message_id(self, event: Event) -> str:
        assert isinstance(event, MessageEvent)
        return f"{event.message_id}"

    @export
    async def text(self, seg: Text, bot: Bot) -> "MessageSegment":
        if not seg.styles:
            return Entity.text(seg.text)
        else:
            style = seg.extract_most_style()
            if style == "link":
                if not getattr(seg, "_children", []):
                    return Entity.url(seg.text)
                else:
                    return Entity.text_link(seg._children[0].text, seg.text)  # type: ignore
            return Entity(STYLE_TYPE_MAP.get(style, style), {"text": seg.text})

    @export
    async def at(self, seg: At, bot: Bot) -> "MessageSegment":
        return (
            Entity.mention(f"{seg.target} ")
            if seg.target.startswith("@")
            else Entity.text_link("用户 ", f"tg://user?id={seg.target}")
        )

    @export
    async def emoji(self, seg: Emoji, bot: Bot) -> "MessageSegment":
        return Entity.custom_emoji(seg.name, seg.id)  # type: ignore

    @export
    async def media(self, seg: Union[Image, Voice, Video, Audio, File], bot: Bot) -> "MessageSegment":
        name = seg.__class__.__name__.lower()
        method = {
            "image": TgFile.photo,
            "voice": TgFile.voice,
            "video": TgFile.video,
            "audio": TgFile.audio,
            "file": TgFile.document,
        }[name]
        if seg.id or seg.url:
            return method(seg.id or seg.url)
        elif seg.path:
            return method(Path(seg.path).read_bytes())
        elif seg.raw:
            return method(seg.raw_bytes)
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type=name, seg=seg))

    @export
    async def reply(self, seg: Reply, bot: Bot) -> "MessageSegment":
        return TgReply.reply(int(seg.id))

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: Message):
        assert isinstance(bot, TgBot)
        assert isinstance(message, TgMessage)
        if isinstance(target, Event):
            assert isinstance(target, TgEvent)
            return await bot.send(event=target, message=message)
        return await bot.send_to(target.id, message)

    async def recall(self, mid: Any, bot: Bot, context: Union[Target, Event]):
        assert isinstance(bot, TgBot)
        _mid: MessageModel = cast(MessageModel, mid)
        await bot.delete_message(chat_id=_mid.chat.id, message_id=_mid.message_id)

    async def edit(self, new: Message, mid: Any, bot: Bot, context: Union[Target, Event]):
        assert isinstance(bot, TgBot)
        _mid: MessageModel = cast(MessageModel, mid)
        text = new.extract_plain_text()
        res = await bot.edit_message_text(text=text, chat_id=_mid.chat.id, message_id=_mid.message_id)
        if isinstance(res, MessageModel):
            return res

    def get_reply(self, mid: Any):
        _mid: MessageModel = cast(MessageModel, mid)
        return Reply(str(_mid.message_id))
