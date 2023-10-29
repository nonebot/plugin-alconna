import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, List, Union

from nonebot.adapters import Bot, Event

from .export import Target, MessageExporter

if TYPE_CHECKING:
    from .message import UniMessage


@dataclass
class Receipt:
    bot: Bot
    context: Union[Event, Target]
    exporter: MessageExporter
    msg_ids: List[Any]

    async def recall(self, delay: float = 0):
        if delay > 1e-4:
            await asyncio.sleep(delay)
        try:
            for msg_id in self.msg_ids:
                if not msg_id:
                    continue
                await self.exporter.recall(msg_id, self.bot, self.context)
            return
        except NotImplementedError:
            return

    async def edit(self, message: "UniMessage", delay: float = 0):
        if delay > 1e-4:
            await asyncio.sleep(delay)
        msg = await self.exporter.export(message, self.bot, True)
        try:
            if not self.msg_ids[0]:
                return self
            res = await self.exporter.edit(msg, self.msg_ids[0], self.bot, self.context)
            if res:
                self.msg_ids = res if isinstance(res, list) else [res]
            return self
        except NotImplementedError:
            return self
