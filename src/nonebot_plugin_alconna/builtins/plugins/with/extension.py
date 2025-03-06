import random
from typing import Any, Callable, ClassVar, Optional

from tarina import LRU
from arclet.alconna import Alconna
from nonebot.internal.adapter import Bot, Event

from nonebot_plugin_alconna import Target, Extension, UniMessage


class PrefixAppendExtension(Extension):
    """用于自动为传入消息增加一个指定前缀"""

    @property
    def priority(self) -> int:
        return 12

    @property
    def id(self) -> str:
        return "builtins.plugins.with.extension:PrefixAppendExtension"

    supplier: ClassVar[Callable[[Any, Target], Optional[str]]]
    prefixes: list[str]
    command: str
    sep: str
    cache: "LRU[str, UniMessage]" = LRU(20)

    def post_init(self, alc: Alconna) -> None:
        self.prefixes = [pf for pf in alc.prefixes if isinstance(pf, str)]
        self.command = alc.header_display
        self.sep = alc.separators[0]

    async def receive_wrapper(self, bot: Bot, event: Event, command: Alconna, receive: UniMessage) -> UniMessage:
        msg_id = UniMessage.get_message_id(event, bot)
        if msg_id in self.cache:
            return self.cache[msg_id]
        target = UniMessage.get_target(event, bot)
        prefix = self.supplier(target)
        if not prefix or not command.header_display.endswith(prefix):
            return receive
        res = UniMessage.text(random.choice(self.prefixes) + prefix + self.sep) + receive
        self.cache[msg_id] = res
        return res
