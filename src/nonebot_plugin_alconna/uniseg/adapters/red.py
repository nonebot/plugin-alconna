from pathlib import Path
from typing import TYPE_CHECKING, Union

from tarina import lang
from nonebot.adapters import Bot, Message
from nonebot.internal.driver import Request

from ..export import Target, MessageExporter, SerializeFailed, export
from ..segment import At, File, Text, AtAll, Audio, Emoji, Image, Reply, Video, Voice, Reference, CustomNode

if TYPE_CHECKING:
    from nonebot.adapters.red.message import MessageSegment


class RedMessageExporter(MessageExporter["MessageSegment"]):
    def get_message_type(self):
        from nonebot.adapters.red.message import Message

        return Message

    @classmethod
    def get_adapter(cls) -> str:
        return "RedProtocol"

    @export
    async def text(self, seg: Text, bot: Bot) -> "MessageSegment":
        ms = self.segment_class
        return ms.text(seg.text)

    @export
    async def at(self, seg: At, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.at(seg.target)

    @export
    async def at_all(self, seg: AtAll, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.at_all()

    @export
    async def emoji(self, seg: Emoji, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.face(seg.id)

    @export
    async def media(self, seg: Union[Image, Voice, Video, Audio, File], bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        name = seg.__class__.__name__.lower()
        method = {
            "image": ms.image,
            "voice": ms.voice,
            "video": ms.video,
            "audio": ms.voice,
            "file": ms.file,
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
    async def reply(self, seg: Reply, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.reply(seg.id)

    @export
    async def reference(self, seg: Reference, bot: Bot) -> "MessageSegment":
        from nonebot.adapters.red.message import ForwardNode

        ms = self.segment_class
        if not seg.content or not isinstance(seg.content, list):
            raise SerializeFailed(
                lang.require("nbp-uniseg", "invalid_segment").format(type="forward", seg=seg)
            )
        nodes = []
        for node in seg.content:
            if not isinstance(node, CustomNode):
                raise SerializeFailed(
                    lang.require("nbp-uniseg", "invalid_segment").format(type="forward", seg=seg)
                )
            content = self.get_message_type()()
            if isinstance(node.content, str):
                content.extend(self.get_message_type()(node.content))
            elif isinstance(node.content, list):
                content.extend(await self.export(node.content, bot, True))  # type: ignore
            else:
                content.extend(node.content)
            nodes.append(ForwardNode(uin=node.uid, name=node.name, time=node.time, message=content))
        return ms.forward(nodes)

    async def send_to(self, target: Target, bot: Bot, message: Message):
        from nonebot.adapters.red.bot import Bot as RedBot

        assert isinstance(bot, RedBot)

        if target.private:
            return await bot.send_friend_message(target=target.id, message=message)
        else:
            return await bot.send_group_message(target=target.id, message=message)
