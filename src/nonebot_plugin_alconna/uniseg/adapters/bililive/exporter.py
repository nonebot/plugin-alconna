from typing import Union

from nonebot.adapters import Bot, Event
from nonebot.adapters.bilibili_live.event import MessageEvent, DanmakuEvent, SuperChatEvent
from nonebot.adapters.bilibili_live.message import Message, MessageSegment
from nonebot.adapters.bilibili_live.bot import WebBot

from nonebot_plugin_alconna.uniseg.constraint import SupportScope
from nonebot_plugin_alconna.uniseg.exporter import MessageExporter, SupportAdapter, Target, export
from nonebot_plugin_alconna.uniseg.segment import At, Emoji, Text, Reply


class BiliLiveMessageExporter(MessageExporter[Message]):
    def get_message_type(self):
        return Message

    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.bililive

    def get_target(self, event: Event, bot: Union[Bot, None] = None) -> Target:

        if isinstance(event, MessageEvent):
            return Target(
                str(event.room_id),
                adapter=self.get_adapter(),
                self_id=bot.self_id if bot else None,
                scope=SupportScope.bililive,
            )
        raise NotImplementedError

    def get_message_id(self, event: Event) -> str:
        if isinstance(event, DanmakuEvent):
            return event.msg_id or f"{event.room_id}:{hash(event.content)}"
        if isinstance(event, SuperChatEvent):
            return str(event.msg_id or event.id)
        raise NotImplementedError

    @export
    async def text(self, seg: Text, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.text(seg.text)

    @export
    async def at(self, seg: At, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.at(seg.target, seg.display)

    @export
    async def emoji(self, seg: Emoji, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.emoticon(seg.id)

    @export
    async def reply(self, seg: Reply, bot: Union[Bot, None]) -> "MessageSegment":
        return MessageSegment.at(seg.id)

    async def send_to(self, target: Union[Target, Event], bot: Bot, message: Message, **kwargs):
        if isinstance(target, Target):
            assert isinstance(bot, WebBot), "BiliLive currently only supports WebBot for sending messages."
            reply_mid = message["at"][-1].data.get("uid", 0) if message["at"] else 0
            msg = "".join(str(seg) for seg in message)
            return await bot.send_danmaku(room_id=int(target.id), msg=msg, reply_mid=reply_mid, **kwargs)
        return await bot.send(target, message=message, **kwargs)  # type: ignore
