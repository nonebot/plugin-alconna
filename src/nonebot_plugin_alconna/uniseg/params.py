from typing import Annotated

from nonebot.typing import T_State
from nonebot.internal.params import Depends
from nonebot.internal.adapter import Bot, Event

from .exporter import Target
from .message import TS, UniMessage
from .constraint import UNISEG_TARGET, UNISEG_MESSAGE, UNISEG_MESSAGE_ID


async def _uni_msg(bot: Bot, event: Event, state: T_State) -> UniMessage:
    if UNISEG_MESSAGE in state:
        return state[UNISEG_MESSAGE]
    return await UniMessage.generate(event=event, bot=bot)


def _target(bot: Bot, event: Event, state: T_State) -> Target:
    if UNISEG_TARGET in state:
        return state[UNISEG_TARGET]
    return UniMessage.get_target(event=event, bot=bot)


def _msg_id(bot: Bot, event: Event, state: T_State) -> str:
    if UNISEG_MESSAGE_ID in state:
        return state[UNISEG_MESSAGE_ID]
    return UniMessage.get_message_id(event=event, bot=bot)


def MessageTarget() -> Target:
    return Depends(_target, use_cache=True)


def UniversalMessage() -> UniMessage:
    return Depends(_uni_msg, use_cache=True)


def MessageId() -> str:
    return Depends(_msg_id, use_cache=True)


def UniversalSegment(t: type[TS], index: int = 0) -> TS:
    async def _uni_seg(bot: Bot, event: Event, state: T_State) -> TS:
        message = await _uni_msg(bot, event, state)
        return message[t, index]

    return Depends(_uni_seg, use_cache=True)


UniMsg = Annotated[UniMessage, UniversalMessage()]
MsgId = Annotated[str, MessageId()]
MsgTarget = Annotated[Target, MessageTarget()]
