from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing_extensions import Self
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, overload

from nonebot.compat import custom_validation
from nonebot.exception import FinishedException
from nonebot.internal.adapter import Bot, Event

from .target import Target
from .exporter import MessageExporter
from .fallback import FallbackStrategy
from .segment import Emoji, Reply, Segment

if TYPE_CHECKING:
    from .message import UniMessage


@custom_validation
@dataclass
class Receipt:
    bot: Bot
    context: Event | Target
    exporter: MessageExporter
    msg_ids: list[Any]
    uni_factory: type[UniMessage]

    @property
    def recallable(self) -> bool:
        return self.exporter.__class__.recall != MessageExporter.recall

    @property
    def editable(self) -> bool:
        return self.exporter.__class__.edit != MessageExporter.edit

    @property
    def reactionable(self) -> bool:
        return self.exporter.__class__.reaction != MessageExporter.reaction

    @overload
    def get_reply(self) -> list[Reply] | None: ...

    @overload
    def get_reply(self, index: int) -> Reply | None: ...

    def get_reply(self, index: int | None = None):
        if not self.msg_ids:
            return None
        if index is None:
            try:
                return [self.exporter.get_reply(msg_id) for msg_id in self.msg_ids]
            except NotImplementedError:
                return None
        try:
            msg_id = self.msg_ids[index]
        except IndexError:
            msg_id = self.msg_ids[0]
        if not msg_id:
            return None
        try:
            return self.exporter.get_reply(msg_id)
        except NotImplementedError:
            return None

    async def recall(self, delay: float = 0, index: int | None = None):
        if not self.msg_ids:
            return self
        if delay > 1e-4:
            await asyncio.sleep(delay)
        if index is None:
            try:
                await asyncio.gather(*(self.exporter.recall(msg_id, self.bot, self.context) for msg_id in self.msg_ids))
            except NotImplementedError:
                pass
            else:
                self.msg_ids.clear()
        else:
            try:
                msg_id = self.msg_ids[index]
            except IndexError:
                msg_id = self.msg_ids[0]
            if not msg_id:
                return self
            try:
                await self.exporter.recall(msg_id, self.bot, self.context)
            except NotImplementedError:
                pass
            else:
                self.msg_ids.remove(msg_id)
        return self

    async def reaction(
        self,
        emoji: str | Emoji,
        delay: float = 0,
        index: int = -1,
        delete: bool = False,
    ):
        if not self.msg_ids:
            return self
        if delay > 1e-4:
            await asyncio.sleep(delay)
        emj = Emoji(emoji) if isinstance(emoji, str) else emoji
        try:
            msg_id = self.msg_ids[index]
        except IndexError:
            msg_id = self.msg_ids[0]
        if not msg_id:
            return self
        try:
            await self.exporter.reaction(emj, msg_id, self.bot, self.context, delete)
        except NotImplementedError:
            pass
        return self

    async def edit(
        self,
        message: str | Iterable[str] | Iterable[Segment] | Iterable[str | Segment] | Segment,
        delay: float = 0,
        index: int = -1,
    ):
        if not self.msg_ids:
            return self
        if delay > 1e-4:
            await asyncio.sleep(delay)
        msg: UniMessage = self.uni_factory(message)
        try:
            msg_id = self.msg_ids[index]
        except IndexError:
            msg_id = self.msg_ids[0]
        if not msg_id:
            return self
        try:
            res = await self.exporter.edit(msg, msg_id, self.bot, self.context)
        except NotImplementedError:
            return self
        else:
            if res:
                if isinstance(res, list):
                    self.msg_ids.remove(msg_id)
                    self.msg_ids.extend(res)
                else:
                    self.msg_ids[index] = res
            return self

    async def send(
        self,
        message: str | Iterable[str] | Iterable[Segment] | Iterable[str | Segment] | Segment,
        fallback: bool | FallbackStrategy = FallbackStrategy.rollback,
        at_sender: str | bool = False,
        reply_to: str | bool | Reply | None = False,
        delay: float = 0,
        **kwargs,
    ):
        if delay > 1e-4:
            await asyncio.sleep(delay)
        msg = self.uni_factory(message)
        res = await msg.send(self.context, self.bot, fallback, at_sender, reply_to, **kwargs)
        self.msg_ids.extend(res.msg_ids)
        return self

    async def reply(
        self,
        message: str | Iterable[str] | Iterable[Segment] | Iterable[str | Segment] | Segment,
        fallback: bool | FallbackStrategy = FallbackStrategy.rollback,
        at_sender: str | bool = False,
        index: int = -1,
        delay: float = 0,
        **kwargs,
    ):
        return await self.send(message, fallback, at_sender, self.get_reply(index), delay, **kwargs)

    async def finish(
        self,
        message: str | Iterable[str] | Iterable[Segment] | Iterable[str | Segment] | Segment,
        fallback: bool | FallbackStrategy = FallbackStrategy.rollback,
        at_sender: str | bool = False,
        reply_to: str | bool | Reply | None = False,
        delay: float = 0,
        **kwargs,
    ):
        await self.send(message, fallback, at_sender, reply_to, delay, **kwargs)
        raise FinishedException

    @classmethod
    def __get_validators__(cls):
        yield cls._validate

    @classmethod
    def _validate(cls, value) -> Self:
        if isinstance(value, cls):
            return value
        raise ValueError(f"Type {type(value)} can not be converted to {cls}")
