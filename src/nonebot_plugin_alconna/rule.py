from __future__ import annotations

import contextlib
from typing import Callable

from arclet.alconna import Alconna, Arparma, Duplication, output_manager
from nonebot.adapters import Event
from nonebot.internal.matcher.matcher import current_bot
from nonebot.internal.rule import Rule as Rule
from nonebot.typing import T_State

from .consts import ALCONNA_RESULT
from .model import CommandResult


class AlconnaRule:
    """检查消息字符串是否能够通过此 Alconna 命令。

    参数:
        command: Alconna 命令
        checker: 命令解析结果的检查器
        duplication: 可选的自定义 Duplication 类型
        skip_for_unmatch: 是否在命令不匹配时跳过该响应
        auto_send_output: 是否自动发送输出信息并跳过响应
    """

    __slots__ = ("command", "duplication", "skip", "checkers", "auto_send")

    def __init__(
        self,
        command: Alconna,
        *checker: Callable[[Arparma], bool],
        duplication: type[Duplication] | None = None,
        skip_for_unmatch: bool = True,
        auto_send_output: bool = False,
    ):
        self.command = command
        self.duplication = duplication
        self.skip = skip_for_unmatch
        self.checkers = checker
        self.auto_send = auto_send_output

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
        if (
            not may_help_text
            and not arp.matched
            and ((not arp.head_matched) or self.skip)
        ):
            return False
        if self.auto_send and may_help_text:
            with contextlib.suppress(LookupError):
                bot = current_bot.get()
                await bot.send(event, may_help_text)
                return False
        for checker in self.checkers:
            if not checker(arp):
                return False
        state[ALCONNA_RESULT] = CommandResult(
            arp.token, may_help_text, self.duplication
        )
        return True


def alconna(
    command: Alconna,
    *checker: Callable[[Arparma], bool],
    duplication: type[Duplication] | None = None,
    skip_for_unmatch: bool = True,
    auto_send_output: bool = False,
) -> Rule:
    return Rule(
        AlconnaRule(
            command,
            *checker,
            duplication=duplication,
            skip_for_unmatch=skip_for_unmatch,
            auto_send_output=auto_send_output
        )
    )
