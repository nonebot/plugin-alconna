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
from nonebot.adapters.telegram.model import InlineKeyboardButton, InlineKeyboardMarkup

from nonebot_plugin_alconna.uniseg.constraint import SupportScope
from nonebot_plugin_alconna.uniseg.exporter import Target, SupportAdapter, MessageExporter, SerializeFailed, export
from nonebot_plugin_alconna.uniseg.segment import (
    At,
    File,
    Text,
    Audio,
    Emoji,
    Image,
    Reply,
    Video,
    Voice,
    Button,
    Keyboard,
)

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
            extra={"message_thread_id": getattr(event, "message_thread_id", None)},
        )

    def get_message_id(self, event: Event) -> str:
        assert isinstance(event, MessageEvent)
        return f"{event.message_id}"

    @export
    async def text(self, seg: Text, bot: Union[Bot, None]):
        if not seg.styles:
            return Entity.text(seg.text)
        style = seg.extract_most_style()
        if style == "link":
            if not getattr(seg, "_children", []):
                return Entity.url(seg.text)
            return Entity.text_link(seg._children[0].text, seg.text)  # type: ignore
        res = []
        for part in seg.style_split():
            style = part.extract_most_style()
            res.append(Entity(STYLE_TYPE_MAP.get(style, style), {"text": part.text}))
        return res

    @export
    async def at(self, seg: At, bot: Union[Bot, None]) -> "MessageSegment":
        return (
            Entity.mention(f"{seg.target} ")
            if seg.target.startswith("@")
            else Entity.text_link("用户 ", f"tg://user?id={seg.target}")
        )

    @export
    async def emoji(self, seg: Emoji, bot: Union[Bot, None]) -> "MessageSegment":
        return Entity.custom_emoji(seg.name, seg.id)  # type: ignore

    @export
    async def media(self, seg: Union[Image, Voice, Video, Audio, File], bot: Union[Bot, None]) -> "MessageSegment":
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
        if seg.path:
            raw = Path(seg.path).read_bytes()
        elif seg.raw:
            raw = seg.raw_bytes
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type=name, seg=seg))
        return method((seg.name, raw) if seg.name else raw)

    @export
    async def reply(self, seg: Reply, bot: Union[Bot, None]) -> "MessageSegment":
        return TgReply.reply(int(seg.id))

    def _button(self, seg: Button, bot: Union[Bot, None]):
        label = str(seg.label)
        if seg.flag == "link":
            return InlineKeyboardButton(text=label, url=seg.url)
        if seg.flag == "action":
            return InlineKeyboardButton(text=label, callback_data=seg.id)
        return InlineKeyboardButton(text=label, switch_inline_query_current_chat=seg.text)

    @export
    async def button(self, seg: Button, bot: Union[Bot, None]):
        return MessageSegment("$telegram:button", {"button": self._button(seg, bot)})

    @export
    async def keyboard(self, seg: Keyboard, bot: Union[Bot, None]):
        if not seg.children:
            return Entity.text("")
        buttons = [self._button(but, bot) for but in seg.children]
        if len(buttons) < 10 and not seg.row:
            return MessageSegment("$telegram:button_row", {"buttons": buttons})
        rows = [buttons[i : i + (seg.row or 9)] for i in range(0, len(buttons), seg.row or 9)]
        return MessageSegment("$telegram:keyboard", {"buttons": rows})

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: Message, **kwargs):
        assert isinstance(bot, TgBot)
        assert isinstance(message, TgMessage)
        reply_markup = None
        if buttons := message.get("$telegram:button"):
            message = message.exclude("$telegram:button")
            buts = [but.data["button"] for but in buttons]
            rows = [buts[i : i + 9] for i in range(0, len(buttons), 9)]
            reply_markup = InlineKeyboardMarkup(inline_keyboard=rows)
        if rows := message.get("$telegram:button_row"):
            message = message.exclude("$telegram:button_row")
            but_rows = [row.data["buttons"] for row in rows]
            if not reply_markup:
                reply_markup = InlineKeyboardMarkup(inline_keyboard=but_rows)
            else:
                reply_markup.inline_keyboard += but_rows
        if kb := message.get("$telegram:keyboard"):
            message = message.exclude("$telegram:keyboard")
            if reply_markup:
                reply_markup.inline_keyboard += kb[0].data["buttons"]
            else:
                reply_markup = InlineKeyboardMarkup(inline_keyboard=kb[0].data["buttons"])
        if isinstance(target, Event):
            assert isinstance(target, TgEvent)
            return await bot.send(event=target, message=message, reply_markup=reply_markup, **kwargs)
        kwargs.setdefault("message_thread_id", target.extra.get("message_thread_id", None))
        return await bot.send_to(target.id, message=message, reply_markup=reply_markup, **kwargs)

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
        return None

    def get_reply(self, mid: Any):
        _mid: MessageModel = cast(MessageModel, mid)
        return Reply(str(_mid.message_id))
