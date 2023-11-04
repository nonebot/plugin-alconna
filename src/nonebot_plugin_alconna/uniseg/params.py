from typing import Type
from typing_extensions import Annotated

from nonebot.internal.params import Depends
from nonebot.internal.adapter import Bot, Event

from .export import Target
from .message import TS, UniMessage


async def _uni_msg(bot: Bot, event: Event) -> UniMessage:
    return await UniMessage.generate(event=event, bot=bot)


def _target(bot: Bot, event: Event) -> Target:
    return UniMessage.get_target(event=event, bot=bot)


def _msg_id(bot: Bot, event: Event) -> str:
    return UniMessage.get_message_id(event=event, bot=bot)


def MessageTarget() -> Target:
    return Depends(_target, use_cache=True)


def UniversalMessage() -> UniMessage:
    return Depends(_uni_msg, use_cache=True)


def MessageId() -> str:
    return Depends(_msg_id, use_cache=True)


def UniversalSegment(t: Type[TS], index: int = 0) -> TS:
    async def _uni_seg(bot: Bot, event: Event) -> TS:
        return (await UniMessage.generate(event=event, bot=bot))[t, index]

    return Depends(_uni_seg, use_cache=True)


UniMsg = Annotated[UniMessage, UniversalMessage()]
MsgId = Annotated[str, MessageId()]
MsgTarget = Annotated[Target, MessageTarget()]
