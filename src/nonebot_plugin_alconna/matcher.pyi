from typing import Callable
from datetime import datetime, timedelta

from nonebot.rule import Rule
from arclet.alconna import Alconna
from nonebot.matcher import Matcher
from nonebot.permission import Permission
from nonebot.dependencies import Dependent
from nonebot.typing import T_State, T_Handler, T_RuleChecker, T_PermissionChecker

from nonebot_plugin_alconna.model import CompConfig
from nonebot_plugin_alconna.typings import MReturn, TConvert

def on_alconna(
    command: Alconna | str,
    rule: Rule | T_RuleChecker | None = None,
    skip_for_unmatch: bool = True,
    auto_send_output: bool = False,
    output_converter: TConvert | None = None,
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
def funcommand(
    name: str | None = None,
    prefixes: list[str] | None = None,
    description: str | None = None,
    rule: Rule | T_RuleChecker | None = None,
    permission: Permission | T_PermissionChecker | None = ...,
    *,
    handlers: list[T_Handler | Dependent] | None = ...,
    temp: bool = ...,
    expire_time: datetime | timedelta | None = ...,
    priority: int = ...,
    block: bool = ...,
    state: T_State | None = ...,
) -> Callable[[Callable[..., MReturn]], type[Matcher]]: ...
