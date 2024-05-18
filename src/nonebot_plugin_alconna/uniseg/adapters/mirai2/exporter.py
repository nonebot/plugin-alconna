from typing import TYPE_CHECKING, Any, Union

from tarina import lang
from nonebot.adapters import Bot, Event
from nonebot.adapters.mirai2.bot import Bot as MiraiBot
from nonebot.adapters.mirai2.message import MessageType, MessageChain, MessageSegment
from nonebot.adapters.mirai2.event import (
    BotMuteEvent,
    GroupMessage,
    MessageEvent,
    FriendMessage,
    BotUnmuteEvent,
    MemberJoinEvent,
    MemberMuteEvent,
    GroupRecallEvent,
    BotJoinGroupEvent,
    BotLeaveEventKick,
    FriendRecallEvent,
    MemberUnmuteEvent,
    BotLeaveEventActive,
    MemberLeaveEventKick,
    MemberLeaveEventQuit,
    GroupStateChangeEvent,
    MemberStateChangeEvent,
)

from nonebot_plugin_alconna.uniseg.constraint import SupportScope
from nonebot_plugin_alconna.uniseg.exporter import Target, SupportAdapter, MessageExporter, SerializeFailed, export
from nonebot_plugin_alconna.uniseg.segment import (
    At,
    File,
    Text,
    AtAll,
    Audio,
    Emoji,
    Hyper,
    Image,
    Reply,
    Voice,
    RefNode,
    Reference,
)


class Mirai2MessageExporter(MessageExporter[MessageChain]):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.mirai_community

    def get_message_type(self):
        return MessageChain

    def get_target(self, event: Event, bot: Union[Bot, None] = None) -> Target:
        if isinstance(event, FriendMessage):
            return Target(
                str(event.sender.id),
                private=True,
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.qq_client,
            )
        elif isinstance(event, GroupMessage):
            return Target(
                str(event.sender.group.id),
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.qq_client,
            )
        elif isinstance(event, (BotMuteEvent, BotUnmuteEvent)):
            return Target(
                str(event.operator.group.id),
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.qq_client,
            )
        elif isinstance(event, (MemberMuteEvent, MemberUnmuteEvent)):
            return Target(
                str(event.member.group.id),
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.qq_client,
            )
        elif isinstance(event, (BotJoinGroupEvent, BotLeaveEventActive, BotLeaveEventKick)):
            return Target(
                str(event.group.id),
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.qq_client,
            )
        elif isinstance(event, (MemberJoinEvent, MemberLeaveEventKick, MemberLeaveEventQuit)):
            return Target(
                str(event.member.group.id),
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.qq_client,
            )
        elif isinstance(event, MemberStateChangeEvent):
            return Target(
                str(event.member.group.id),
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.qq_client,
            )
        elif isinstance(event, GroupStateChangeEvent):
            return Target(
                str(event.group.id),
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.qq_client,
            )
        elif isinstance(event, FriendRecallEvent):
            return Target(
                str(event.author_id),
                private=True,
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.qq_client,
            )
        elif isinstance(event, GroupRecallEvent):
            return Target(
                str(event.group.id),
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.qq_client,
            )
        raise NotImplementedError

    def get_message_id(self, event: Event) -> str:
        assert isinstance(event, MessageEvent)
        return str(event.source and event.source.id)

    @export
    async def text(self, seg: Text, bot: Bot) -> "MessageSegment":
        return MessageSegment.plain(seg.text)

    @export
    async def at(self, seg: At, bot: Bot) -> "MessageSegment":
        return MessageSegment.at(int(seg.target))

    @export
    async def at_all(self, seg: AtAll, bot: Bot) -> "MessageSegment":
        return MessageSegment.at_all()

    @export
    async def emoji(self, seg: Emoji, bot: Bot) -> "MessageSegment":
        return MessageSegment.face(int(seg.id), seg.name)

    @export
    async def media(self, seg: Union[Image, Voice, Audio], bot: Bot) -> "MessageSegment":
        name = seg.__class__.__name__.lower()
        method = {
            "image": MessageSegment.image,
            "voice": MessageSegment.voice,
            "audio": MessageSegment.voice,
        }[name]
        if seg.id:
            return method(seg.id)
        elif seg.url:
            return method(url=seg.url)
        elif seg.path:
            return method(path=str(seg.path))
        elif seg.__class__.to_url and seg.raw:
            return method(
                url=await seg.__class__.to_url(seg.raw, bot, None if seg.name == seg.__default_name__ else seg.name)
            )
        else:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type=name, seg=seg))

    @export
    async def file(self, seg: File, bot: Bot) -> "MessageSegment":
        return MessageSegment.file(seg.id, seg.name, 0)  # type: ignore

    @export
    async def hyper(self, seg: Hyper, bot: Bot) -> "MessageSegment":
        assert seg.raw, lang.require("nbp-uniseg", "invalid_segment").format(type="hyper", seg=seg)
        return MessageSegment.xml(seg.raw) if seg.format == "xml" else MessageSegment.app(seg.raw)

    @export
    async def reply(self, seg: Reply, bot: Bot) -> "MessageSegment":
        return MessageSegment("$reply", {"message_id": seg.id})  # type: ignore

    @export
    async def reference(self, seg: Reference, bot: Bot) -> "MessageSegment":
        if not seg.children:
            raise SerializeFailed(lang.require("nbp-uniseg", "invalid_segment").format(type="forward", seg=seg))
        nodes = []
        for node in seg.children:
            if isinstance(node, RefNode):
                if node.context:
                    nodes.append({"messageRef": {"messageId": node.id, "target": node.context}})
                else:
                    nodes.append({"messageId": node.id})
            else:
                content = self.get_message_type()([])
                if isinstance(node.content, str):
                    content.extend(self.get_message_type()(node.content))
                elif isinstance(node.content, list):
                    content.extend(await self.export(node.content, bot, True))  # type: ignore
                else:
                    content.extend(node.content)
                nodes.append(
                    {
                        "senderId": node.uid,
                        "senderName": node.name,
                        "time": int(node.time.timestamp()),
                        "messageChain": content,
                    }
                )
        return MessageSegment(MessageType.FORWARD, nodeList=nodes)

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: MessageChain):
        assert isinstance(bot, MiraiBot)
        if TYPE_CHECKING:
            assert isinstance(message, self.get_message_type())

        if message.has("Quote"):
            quote = message.pop(message.index("Quote")).data["id"]
        else:
            quote = None

        if isinstance(target, Event):
            target = self.get_target(target, bot)

        if target.private:
            return await bot.send_friend_message(target=int(target.id), message_chain=message, quote=quote)
        else:
            return await bot.send_group_message(target=int(target.id), message_chain=message, quote=quote)

    async def recall(self, mid: Any, bot: Bot, context: Union[Target, Event]):
        assert isinstance(bot, MiraiBot)
        await bot.recall(target=mid["messageId"])
        return

    def get_reply(self, mid: Any):
        return Reply(str(mid["messageId"]))
