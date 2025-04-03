from __future__ import annotations

from typing import TYPE_CHECKING

from tarina import lang
from nonebot.adapters import Bot, Event
from nonebot.internal.matcher import current_bot, current_event

from .segment import Emoji
from .exporter import SerializeFailed
from .adapters import alter_get_exporter

if TYPE_CHECKING:
    from .target import Target
    from .message import UniMessage


async def message_recall(
    message_id: str | None = None, event: Event | None = None, bot: Bot | None = None, adapter: str | None = None
):
    if not event:
        try:
            event = current_event.get()
        except LookupError as e:
            raise SerializeFailed(lang.require("nbp-uniseg", "event_missing")) from e
    if not bot:
        try:
            bot = current_bot.get()
        except LookupError as e:
            raise SerializeFailed(lang.require("nbp-uniseg", "bot_missing")) from e
    if not adapter:
        _adapter = bot.adapter
        adapter = _adapter.get_name()
    if fn := alter_get_exporter(adapter):
        try:
            return await fn.recall(message_id or fn.get_message_id(event), bot, event)
        except NotImplementedError:
            return
    raise SerializeFailed(lang.require("nbp-uniseg", "unsupported").format(adapter=adapter))


async def message_edit(
    msg: UniMessage,
    message_id: str | None = None,
    event: Event | None = None,
    bot: Bot | None = None,
    adapter: str | None = None,
):
    if not event:
        try:
            event = current_event.get()
        except LookupError as e:
            raise SerializeFailed(lang.require("nbp-uniseg", "event_missing")) from e
    if not bot:
        try:
            bot = current_bot.get()
        except LookupError as e:
            raise SerializeFailed(lang.require("nbp-uniseg", "bot_missing")) from e
    if not adapter:
        _adapter = bot.adapter
        adapter = _adapter.get_name()
    if fn := alter_get_exporter(adapter):
        try:
            return await fn.edit(msg, message_id or fn.get_message_id(event), bot, event)
        except NotImplementedError:
            return
    raise SerializeFailed(lang.require("nbp-uniseg", "unsupported").format(adapter=adapter))


async def message_reaction(
    emoji: str | Emoji,
    message_id: str | None = None,
    event: Event | None = None,
    bot: Bot | None = None,
    adapter: str | None = None,
    delete: bool = False,
):
    if not event:
        try:
            event = current_event.get()
        except LookupError as e:
            raise SerializeFailed(lang.require("nbp-uniseg", "event_missing")) from e
    if not bot:
        try:
            bot = current_bot.get()
        except LookupError as e:
            raise SerializeFailed(lang.require("nbp-uniseg", "bot_missing")) from e
    if not adapter:
        _adapter = bot.adapter
        adapter = _adapter.get_name()
    emj = Emoji(emoji) if isinstance(emoji, str) else emoji
    if fn := alter_get_exporter(adapter):
        try:
            return await fn.reaction(emj, message_id or fn.get_message_id(event), bot, event, delete=delete)
        except NotImplementedError:
            return
    raise SerializeFailed(lang.require("nbp-uniseg", "unsupported").format(adapter=adapter))


def get_message_id(event: Event | None = None, bot: Bot | None = None, adapter: str | None = None) -> str:
    if not event:
        try:
            event = current_event.get()
        except LookupError as e:
            raise SerializeFailed(lang.require("nbp-uniseg", "event_missing")) from e
    if hasattr(event, "__uniseg_message_id__"):
        return event.__uniseg_message_id__  # type: ignore
    if not adapter:
        if not bot:
            try:
                bot = current_bot.get()
            except LookupError as e:
                raise SerializeFailed(lang.require("nbp-uniseg", "bot_missing")) from e
        _adapter = bot.adapter
        adapter = _adapter.get_name()
    if fn := alter_get_exporter(adapter):
        setattr(event, "__uniseg_message_id__", msg_id := fn.get_message_id(event))
        return msg_id
    raise SerializeFailed(lang.require("nbp-uniseg", "unsupported").format(adapter=adapter))


def get_target(event: Event | None = None, bot: Bot | None = None, adapter: str | None = None) -> Target:
    if not event:
        try:
            event = current_event.get()
        except LookupError as e:
            raise SerializeFailed(lang.require("nbp-uniseg", "event_missing")) from e
    if not adapter:
        if not bot:
            try:
                bot = current_bot.get()
            except LookupError as e:
                raise SerializeFailed(lang.require("nbp-uniseg", "bot_missing")) from e
        _adapter = bot.adapter
        adapter = _adapter.get_name()
    if fn := alter_get_exporter(adapter):
        return fn.get_target(event, bot)
    raise SerializeFailed(lang.require("nbp-uniseg", "unsupported").format(adapter=adapter))
