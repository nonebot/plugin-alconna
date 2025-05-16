from __future__ import annotations

from tarina import LRU
from nonebot.typing import T_State
from nonebot.adapters.onebot.v11 import Message
from nonebot.internal.adapter import Bot, Event
from nonebot.adapters.onebot.v11 import Event as OneBot11Event

from nonebot_plugin_alconna.extension import cache_msg
from nonebot_plugin_alconna import Extension, UniMessage, get_message_id


class MessageSentExtension(Extension):
    """
    用于提取自身上报消息事件中的消息内容

    推荐配合 `add_global_extension` 使用

    注意: 该扩展仅提供消息内容，无法配置 Alconna 响应器响应自身消息。

    Example:
        >>> from nonebot_plugin_alconna import add_global_extension
        >>> from nonebot_plugin_alconna.builtins.extensions.onebot11 import MessageSentExtension
        >>>
        >>> add_global_extension(MessageSentExtension())
    """

    cache: LRU[str, UniMessage] = LRU(20)

    @property
    def priority(self) -> int:
        return 8

    @property
    def id(self) -> str:
        return "builtins.extensions.onebot11:MessageSentExtension"

    def validate(self, bot: Bot, event: Event) -> bool:
        return isinstance(event, OneBot11Event) and event.get_type() == "message_sent"

    async def message_provider(
        self, event: Event, state: T_State, bot: Bot, use_origin: bool = False
    ) -> UniMessage | None:
        if event.get_type() == "message_sent" and hasattr(event, "message"):
            msg_id = get_message_id(event, bot)
            if use_origin and cache_msg and (uni_msg := self.cache.get(msg_id)) is not None:
                return uni_msg
            if cache_msg and (uni_msg := self.cache.get(msg_id)) is not None:
                return uni_msg
            msg = Message._validate(event.message)  # type: ignore
            uni_msg = UniMessage.generate_without_reply(message=msg, bot=bot)
            self.cache[msg_id] = uni_msg
            return uni_msg
        return None
