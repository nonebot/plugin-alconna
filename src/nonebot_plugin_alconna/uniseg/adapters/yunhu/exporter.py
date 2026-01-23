from pathlib import Path
from typing import TYPE_CHECKING, Any, Sequence, Union, cast

from nonebot.adapters import Bot, Event
from nonebot.adapters.yunhu.bot import Bot as YunHuBot
from nonebot.adapters.yunhu.event import Event as YunHuEvent
from nonebot.adapters.yunhu.event import MessageEvent, NoticeEvent
from nonebot.adapters.yunhu.message import Message, MessageSegment
from nonebot.adapters.yunhu.models import BaseNotice, ButtonBody, SendMsgResponse
from tarina import lang

from nonebot_plugin_alconna.uniseg.constraint import SupportScope
from nonebot_plugin_alconna.uniseg.exporter import MessageExporter, SerializeFailed, SupportAdapter, Target, export
from nonebot_plugin_alconna.uniseg.segment import At, Button, Emoji, File, Image, Keyboard, Reply, Segment, Text, Video


class YunHuMessageExporter(MessageExporter[Message]):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.yunhu

    def get_message_type(self):
        return Message

    def get_target(self, event: Event, bot: Union[Bot, None] = None) -> Target:
        if isinstance(event, MessageEvent):
            return Target(
                event.event.sender.senderId,
                event.event.chat.chatId if event.event.chat.chatType == "group" else "",
                private=(event.event.chat.chatType == "bot"),
                source=event.event.message.msgId,
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.yunhu,
            )
        if isinstance(event, NoticeEvent):
            if TYPE_CHECKING:
                assert isinstance(event.event, BaseNotice)
            return Target(
                event.get_user_id(),
                event.event.chatId,
                private=(event.event.chatType == "user"),
                source=event.header.eventId,
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.yunhu,
            )
        raise NotImplementedError

    def get_message_id(self, event: Event) -> str:
        assert isinstance(
            event,
            MessageEvent,
        )
        return event.event.message.msgId

    @export
    async def text(self, seg: Text, bot: Union[Bot, None]) -> "MessageSegment":
        if seg.extract_most_style() == "markdown":
            return MessageSegment.markdown(seg.text)
        if seg.extract_most_style() == "html":
            return MessageSegment.html(seg.text)
        if seg.styles:
            return MessageSegment.markdown(str(seg))
        return MessageSegment.text(seg.text)

    @export
    async def at(self, seg: At, bot: Union[Bot, None]) -> "MessageSegment":
        if seg.flag == "user":
            return MessageSegment.at(seg.target, seg.display or "")
        raise SerializeFailed(
            lang.require("nbp-uniseg", "failed_segment").format(adapter="yunhu", seg=seg, target="at")
        )

    @export
    async def face(self, seg: Emoji, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.face(seg.id, seg.name or "")

    @export
    async def media(self, seg: Union[Image, Video, File], bot: Union[Bot, None]) -> "MessageSegment":
        name = seg.__class__.__name__.lower()
        method = {
            "image": MessageSegment.image,
            "video": MessageSegment.video,
            "file": MessageSegment.file,
        }[name]

        if seg.url:
            return method(url=seg.url)
        if seg.raw:
            return method(raw=seg.raw_bytes)
        if seg.path:
            return method(raw=Path(seg.path).read_bytes())
        raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="image", seg=seg))

    @export
    async def reply(self, seg: Reply, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment("$yunhu:reply", {"message_id": seg.id})

    def _button(self, seg: Button, bot: Union[Bot, None]) -> ButtonBody:
        label = str(seg.label)
        if seg.flag == "link":
            return {"text": label, "actionType": 1, "url": seg.url}  # pyright: ignore[reportReturnType]
        if seg.flag == "action":
            return {"text": label, "actionType": 3}  # pyright: ignore[reportReturnType]
        return {"text": label, "actionType": 2, "value": seg.text}  # pyright: ignore[reportReturnType]

    @export
    async def button(self, seg: Button, bot: Union[Bot, None]):
        return MessageSegment("$yunhu:button", {"button": self._button(seg, bot)})

    @export
    async def keyboard(self, seg: Keyboard, bot: Union[Bot, None]):
        if not seg.children:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="keyboard", seg=seg))
        buttons = [self._button(but, bot) for but in seg.children]
        if not seg.row:
            return MessageSegment("$yunhu:button_row", {"buttons": buttons})
        rows = [buttons[i : i + (seg.row or 9)] for i in range(0, len(buttons), seg.row or 9)]
        return MessageSegment("$yunhu:keyboard", {"buttons": rows})

    async def send_to(self, target: Union[Target, YunHuEvent], bot: Bot, message: Message, **kwargs):
        assert isinstance(bot, YunHuBot)
        if TYPE_CHECKING:
            assert isinstance(message, self.get_message_type())

        kb = None
        message_id: str | None = None

        # 处理 button
        if buttons := message.get("$yunhu:button"):
            message = message.exclude("$yunhu:button")
            buts = [but.data["button"] for but in buttons]
            kb = [buts[i : i + 9] for i in range(0, len(buts), 9)]

        # 处理 button_row
        if rows := message.get("$yunhu:button_row"):
            message = message.exclude("$yunhu:button_row")
            but_rows = [row.data["buttons"] for row in rows]
            if not kb:
                kb = but_rows
            else:
                kb.extend(but_rows)

        # 处理 keyboard
        if keyboard := message.get("$yunhu:keyboard"):
            message = message.exclude("$yunhu:keyboard")
            keyboard_buttons = keyboard[0].data["buttons"]
            if not kb:
                kb = keyboard_buttons
            else:
                kb.extend(keyboard_buttons)

        if kb:
            message.append(MessageSegment.buttons(kb))

        # 处理 reply
        if reply_segments := message.get("$yunhu:reply"):
            message = message.exclude("$yunhu:reply")
            raw_inner_id = reply_segments[0].data.get("message_id")
            message_id = str(raw_inner_id) if raw_inner_id else None
        else:
            message_id = None

        if isinstance(target, YunHuEvent):
            if message_id:
                return await bot.send(event=target, message=message, reply_to=message_id)
            return await bot.send(event=target, message=message)

        content, content_type = message.serialize()
        return await bot.send_msg(
            receive_type=("user" if target.private else "group"),
            receive_id=target.id,
            content=content,
            content_type=content_type,
            parent_id=message_id,
        )

    async def recall(self, mid: Any, bot: Bot, context: Union[Target, Event]):
        assert isinstance(bot, YunHuBot)
        if isinstance(mid, (str, int)) and isinstance(context, MessageEvent):
            if context.event.message.chatType == "bot":
                chat_id = context.event.sender.senderId
                chat_type = "user"
            else:
                chat_id = context.event.message.chatId
                chat_type = "group"
            await bot.delete_msg(message_id=str(mid), chat_id=chat_id, chat_type=chat_type)
        else:
            _mid: SendMsgResponse = cast(SendMsgResponse, mid)
            assert _mid.data
            await bot.delete_msg(
                message_id=_mid.data.messageInfo.msgId,
                chat_id=_mid.data.messageInfo.recvId,
                chat_type=_mid.data.messageInfo.recvType,
            )

    async def edit(self, new: Sequence[Segment], mid: Any, bot: Bot, context: Union[Target, Event]):
        assert isinstance(bot, YunHuBot)
        new_msg = await self.export(new, bot, True)
        content, _type = new_msg.serialize()
        if isinstance(mid, (str, int)) and isinstance(context, MessageEvent):
            if context.event.message.chatType == "bot":
                chat_id = context.event.sender.senderId
                chat_type = "user"
            else:
                chat_id = context.event.message.chatId
                chat_type = "group"
            await bot.edit_msg(
                message_id=str(mid),
                recvId=chat_id,
                recvType=chat_type,
                content=content,  # pyright: ignore[reportArgumentType]
                content_type=_type,  # pyright: ignore[reportArgumentType]
            )
        else:
            _mid: SendMsgResponse = cast(SendMsgResponse, mid)
            assert _mid.data
            await bot.edit_msg(
                message_id=_mid.data.messageInfo.msgId,
                recvId=_mid.data.messageInfo.recvId,
                recvType=_mid.data.messageInfo.recvType,
                content=content,  # pyright: ignore[reportArgumentType]
                content_type=_type,  # pyright: ignore[reportArgumentType]
            )

    def get_reply(self, mid: Any):
        if isinstance(mid, MessageEvent):
            return Reply(mid.event.message.msgId)
        raise NotImplementedError
