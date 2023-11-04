from pathlib import Path
from typing import TYPE_CHECKING, Any, Union

from tarina import lang
from nonebot.internal.driver import Request
from nonebot.adapters import Bot, Event, Message

from ..export import Target, MessageExporter, SerializeFailed, export
from ..segment import At, Card, Text, AtAll, Audio, Emoji, Image, Reply, Video, Voice, RefNode, Reference

if TYPE_CHECKING:
    from nonebot.adapters.onebot.v11.message import MessageSegment


class Onebot11MessageExporter(MessageExporter["MessageSegment"]):
    def get_message_type(self):
        from nonebot.adapters.onebot.v11.message import Message

        return Message

    @classmethod
    def get_adapter(cls) -> str:
        return "OneBot V11"

    def get_target(self, event: Event) -> Target:
        if group_id := getattr(event, "group_id", None):
            return Target(str(group_id))
        if user_id := getattr(event, "user_id", None):
            return Target(str(user_id), private=True)
        raise NotImplementedError

    def get_message_id(self, event: Event) -> str:
        from nonebot.adapters.onebot.v11.event import MessageEvent

        assert isinstance(event, MessageEvent)
        return str(event.message_id)

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

        return ms.at("all")

    @export
    async def emoji(self, seg: Emoji, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.face(int(seg.id))

    @export
    async def media(self, seg: Union[Image, Voice, Video, Audio], bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        name = seg.__class__.__name__.lower()
        method = {
            "image": ms.image,
            "voice": ms.record,
            "video": ms.video,
            "audio": ms.record,
        }[name]
        if seg.raw:
            return method(seg.raw_bytes)
        elif seg.path:
            return method(Path(seg.path))
        elif seg.url:
            resp = await bot.adapter.request(Request("GET", seg.url))
            return method(resp.content)
        elif seg.id:
            return method(seg.id)
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type=name, seg=seg))

    @export
    async def card(self, seg: Card, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.xml(seg.raw) if seg.flag == "xml" else ms.json(seg.raw)

    @export
    async def reply(self, seg: Reply, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        return ms.reply(int(seg.id))

    @export
    async def reference(self, seg: Reference, bot: Bot) -> "MessageSegment":
        ms = self.segment_class

        if seg.id:
            return ms.forward(seg.id)

        if not seg.content or not isinstance(seg.content, list):
            raise SerializeFailed(
                lang.require("nbp-uniseg", "invalid_segment").format(type="forward", seg=seg)
            )

        nodes = []
        for node in seg.content:
            if isinstance(node, RefNode):
                nodes.append(ms.node(int(node.id)))
            else:
                content = self.get_message_type()()
                if isinstance(node.content, str):
                    content.extend(self.get_message_type()(node.content))
                elif isinstance(node.content, list):
                    content.extend(await self.export(node.content, bot, True))  # type: ignore
                else:
                    content.extend(node.content)
                nodes.append(ms.node_custom(user_id=node.uid, nickname=node.name, content=content))  # type: ignore
        return nodes  # type: ignore

    async def send_to(self, target: Target, bot: Bot, message: Message):
        from nonebot.adapters.onebot.v11.bot import Bot as OnebotBot

        assert isinstance(bot, OnebotBot)
        if TYPE_CHECKING:
            assert isinstance(message, self.get_message_type())

        if target.private:
            return await bot.send_msg(message_type="private", user_id=int(target.id), message=message)
        else:
            return await bot.send_msg(message_type="group", group_id=int(target.id), message=message)

    async def recall(self, mid: Any, bot: Bot, context: Union[Target, Event]):
        from nonebot.adapters.onebot.v11.bot import Bot as OnebotBot

        assert isinstance(bot, OnebotBot)
        await bot.delete_msg(message_id=mid["message_id"])
        return
