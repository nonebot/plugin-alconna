import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, List, Union

from nonebot.adapters import Bot, Event

from .segment import Reply
from .export import Target, MessageExporter

if TYPE_CHECKING:
    from .message import UniMessage


@dataclass
class Receipt:
    bot: Bot
    context: Union[Event, Target]
    exporter: MessageExporter
    msg_ids: List[Any]

    def reply(self, index: int = -1) -> Union[Reply, None]:
        if not self.msg_ids:
            return
        try:
            msg_id = self.msg_ids[index]
        except IndexError:
            msg_id = self.msg_ids[0]
        if not msg_id:
            return
        try:
            return self.exporter.get_reply(msg_id)
        except NotImplementedError:
            return

    async def recall(self, delay: float = 0, index: int = -1):
        if not self.msg_ids:
            return
        if delay > 1e-4:
            await asyncio.sleep(delay)
        try:
            msg_id = self.msg_ids[index]
        except IndexError:
            msg_id = self.msg_ids[0]
        if not msg_id:
            return
        try:
            await self.exporter.recall(msg_id, self.bot, self.context)
            self.msg_ids.remove(msg_id)
        except NotImplementedError:
            return

    async def edit(self, message: "UniMessage", delay: float = 0, index: int = -1):
        if not self.msg_ids:
            return self
        if delay > 1e-4:
            await asyncio.sleep(delay)
        msg = await self.exporter.export(message, self.bot, True)
        try:
            msg_id = self.msg_ids[index]
        except IndexError:
            msg_id = self.msg_ids[0]
        if not msg_id:
            return self
        try:
            res = await self.exporter.edit(msg, msg_id, self.bot, self.context)
            if res:
                if isinstance(res, list):
                    self.msg_ids.remove(msg_id)
                    self.msg_ids.extend(res)
                else:
                    self.msg_ids[index] = res
            return self
        except NotImplementedError:
            return self
