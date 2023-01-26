from __future__ import annotations

from arclet.alconna import Alconna, Duplication, output_manager, Arparma
from nonebot.internal.rule import Rule as Rule
from nonebot.typing import T_State
from nonebot.adapters import Event
from .model import AlconnaCommandResult
from .consts import ALCONNA_RESULT


class AlconnaRule:
    """检查消息字符串是否能够通过此 Alconna 命令。

    参数:
        command: Alconna 命令
        duplication: 可选的自定义 Duplication 类型
    """

    __slots__ = ("command", "duplication", "skip")

    def __init__(
        self,
        command: Alconna,
        duplication: type[Duplication] | None = None,
        skip_for_unmatch: bool = True,
    ):
        self.command = command
        self.duplication = duplication
        self.skip = skip_for_unmatch

    def __repr__(self) -> str:
        return f"Alconna(command={self.command!r}, duplication={self.duplication})"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, AlconnaRule)
            and self.command.path == other.command.path
            and self.duplication == other.duplication
        )

    def __hash__(self) -> int:
        return hash((self.command.__hash__(), self.duplication))

    async def __call__(self, event: Event, state: T_State) -> bool:
        if event.get_type() != "message":
            return False
        try:
            msg = event.get_message()
        except Exception:
            return False
        with output_manager.capture(self.command.name) as cap:
            output_manager.set_action(lambda x: x, self.command.name)
            try:
                arp = self.command.parse(msg)
            except Exception as e:
                arp = Arparma(self.command.path, msg, False, error_info=repr(e))
        may_help_text: str | None = cap.get("output", None)
        if not may_help_text and not arp.matched and ((not arp.head_matched) or self.skip):
            return False
        if not may_help_text and arp.error_info:
            may_help_text = arp.error_info.strip("'").strip("\\n").split("\\n")[-1]
        state[ALCONNA_RESULT] = AlconnaCommandResult(
            arp.token,
            may_help_text,
            self.duplication
        )
        return True


def alconna(
    command: Alconna,
    duplication: type[Duplication] | None = None,
    skip_for_unmatch: bool = True,
) -> Rule:
    return Rule(AlconnaRule(command, duplication, skip_for_unmatch))
