import random
from typing import Any, Callable, ClassVar, Optional

from arclet.alconna import Alconna
from nonebot.typing import T_State
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

    def post_init(self, alc: Alconna) -> None:
        self.prefixes = [pf for pf in alc.prefixes if isinstance(pf, str)]
        self.command = alc.header_display
        self.sep = alc.separators[0]

    async def message_provider(self, event: Event, state: T_State, bot: Bot, use_origin: bool = False):
        if event.get_type() != "message":
            return None
        try:
            msg = event.get_message()
        except (NotImplementedError, ValueError):
            return None
        uni_msg = UniMessage.generate_sync(message=msg, bot=bot)
        target = UniMessage.get_target(event, bot)
        prefix = self.supplier(target)  # type: ignore
        if not prefix or not self.command.endswith(prefix):
            return uni_msg
        return f"{random.choice(self.prefixes)}{prefix}{self.sep}" + uni_msg
