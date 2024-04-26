from pathlib import Path
from typing import TYPE_CHECKING, Any, Union, cast

from tarina import lang
from nonebot.adapters import Bot, Event
from nonebot.internal.driver import Request
from nonebot.adapters.red.bot import Bot as RedBot
from nonebot.adapters.red.api.model import ChatType
from nonebot.adapters.red.event import MessageEvent
from nonebot.adapters.red.api.model import Message as MessageModel
from nonebot.adapters.red.message import Message, ForwardNode, MessageSegment

from nonebot_plugin_alconna.uniseg.constraint import SupportScope
from nonebot_plugin_alconna.uniseg.exporter import Target, SupportAdapter, MessageExporter, SerializeFailed, export
from nonebot_plugin_alconna.uniseg.segment import (
    At,
    File,
    Text,
    AtAll,
    Audio,
    Emoji,
    Image,
    Reply,
    Video,
    Voice,
    Reference,
    CustomNode,
)


class RedMessageExporter(MessageExporter[Message]):
    def get_message_type(self):
        return Message

    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.red

    def get_target(self, event: Event, bot: Union[Bot, None] = None) -> Target:
        assert isinstance(event, MessageModel)
        return Target(
            str(event.peerUin or event.peerUid),
            private=event.chatType == ChatType.FRIEND,
            adapter=self.get_adapter(),
            self_id=bot.self_id if bot else None,
            scope=SupportScope.qq_client,
        )

    def get_message_id(self, event: Event) -> str:
        assert isinstance(event, MessageEvent)
        return f"{event.msgId}#{event.msgSeq}"

    @export
    async def text(self, seg: Text, bot: Bot) -> "MessageSegment":
        return MessageSegment.text(seg.text)

    @export
    async def at(self, seg: At, bot: Bot) -> "MessageSegment":
        return MessageSegment.at(seg.target)

    @export
    async def at_all(self, seg: AtAll, bot: Bot) -> "MessageSegment":
        return MessageSegment.at_all()

    @export
    async def emoji(self, seg: Emoji, bot: Bot) -> "MessageSegment":
        return MessageSegment.face(seg.id)

    @export
    async def media(self, seg: Union[Image, Video, File], bot: Bot) -> "MessageSegment":
        name = seg.__class__.__name__.lower()
        method = {
            "image": MessageSegment.image,
            "video": MessageSegment.video,
            "file": MessageSegment.file,
        }[name]
        if seg.path:
            return method(Path(seg.path))
        elif seg.raw:
            return method(seg.raw_bytes)
        elif seg.url:
            resp = await bot.adapter.request(Request("GET", seg.url))
            return method(resp.content)  # type: ignore
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type=name, seg=seg))

    @export
    async def voice(self, seg: Union[Voice, Audio], bot: Bot) -> "MessageSegment":
        name = seg.__class__.__name__.lower()
        if seg.path:
            return MessageSegment.voice(Path(seg.path), duration=seg.duration or 1)
        elif seg.raw:
            return MessageSegment.voice(seg.raw_bytes, duration=seg.duration or 1)
        elif seg.url:
            resp = await bot.adapter.request(Request("GET", seg.url))
            return MessageSegment.voice(resp.content, duration=seg.duration or 1)  # type: ignore
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type=name, seg=seg))

    @export
    async def reply(self, seg: Reply, bot: Bot) -> "MessageSegment":
        if "#" in seg.id:
            _id, _seq = seg.id.split("#", 1)
            return MessageSegment.reply(_seq, _id)
        return MessageSegment.reply(seg.id)

    @export
    async def reference(self, seg: Reference, bot: Bot) -> "MessageSegment":
        if not seg.children:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="forward", seg=seg))
        nodes = []
        for node in seg.children:
            if not isinstance(node, CustomNode):
                raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="forward", seg=seg))
            content = self.get_message_type()()
            if isinstance(node.content, str):
                content.extend(self.get_message_type()(node.content))
            elif isinstance(node.content, list):
                content.extend(await self.export(node.content, bot, True))  # type: ignore
            else:
                content.extend(node.content)
            nodes.append(ForwardNode(uin=node.uid, name=node.name, time=node.time, message=content))
        return MessageSegment.forward(nodes)

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: Message):
        assert isinstance(bot, RedBot)
        if TYPE_CHECKING:
            assert isinstance(message, self.get_message_type())

        if isinstance(target, Event):
            target = self.get_target(target, bot)

        if target.private:
            return await bot.send_friend_message(target=target.id, message=message)
        else:
            return await bot.send_group_message(target=target.id, message=message)

    async def recall(self, mid: Any, bot: Bot, context: Union[Target, Event]):
        assert isinstance(bot, RedBot)
        _mid: MessageModel = cast(MessageModel, mid)
        await bot.recall_message(_mid.chatType, _mid.peerUin, _mid.msgId)
        return

    def get_reply(self, mid: Any):
        _mid: MessageModel = cast(MessageModel, mid)
        return Reply(f"{_mid.msgId}#{_mid.msgSeq}")
