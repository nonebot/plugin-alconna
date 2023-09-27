from typing import Type
from typing_extensions import Annotated

from nonebot.internal.params import Depends
from nonebot.internal.adapter import Bot, Event

from .message import TS, UniMessage


async def _uni_msg(bot: Bot, event: Event) -> UniMessage:
    return await UniMessage.generate(event, bot)


def UniversalMessage() -> UniMessage:
    return Depends(_uni_msg, use_cache=True)


def UniversalSegment(t: Type[TS], index: int = 0) -> TS:
    async def _uni_seg(bot: Bot, event: Event) -> TS:
        return (await UniMessage.generate(event, bot))[t, index]

    return Depends(_uni_seg, use_cache=True)


UniMsg = Annotated[UniMessage, UniversalMessage()]
