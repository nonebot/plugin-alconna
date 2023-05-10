from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable

from arclet.alconna import Alconna, Arparma
from nonebot.adapters import Message
from nonebot.dependencies import Dependent
from nonebot.matcher import Matcher
from nonebot.permission import Permission
from nonebot.rule import Rule
from nonebot.typing import T_Handler, T_PermissionChecker, T_RuleChecker, T_State
from nonebot_plugin_alconna.typings import OutputType
from nonebot_plugin_alconna.model import CompConfig

def match_path(path: str): ...
def match_value(path: str, value: Any, or_not: bool = False): ...
def assign(
    path: str, value: Any = ..., or_not: bool = False
) -> Callable[[Arparma], bool]: ...
def on_alconna(
    command: Alconna | str,
    checker: list[Callable[[Arparma], bool]] | None = None,
    rule: Rule | T_RuleChecker | None = None,
    skip_for_unmatch: bool = True,
    auto_send_output: bool = False,
    output_converter: Callable[[OutputType, str], Message | Awaitable[Message]] | None = None,
    aliases: set[str | tuple[str, ...]] | None = None,
    comp_config: CompConfig | None = None,
    permission: Permission | T_PermissionChecker | None = ...,
    *,
    handlers: list[T_Handler | Dependent] | None = ...,
    temp: bool = ...,
    expire_time: datetime | timedelta | None = ...,
    priority: int = ...,
    block: bool = ...,
    state: T_State | None = ...,
) -> type[Matcher]: ...
