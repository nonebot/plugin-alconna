from __future__ import annotations

import asyncio
from typing import Protocol

from arclet.alconna import Arparma, CompSession, SubcommandResult
from nonebot.internal.adapter import Bot, Event

from nonebot_plugin_alconna import Extension


class Checker(Protocol):
    async def __call__(self, bot: Bot, event: Event, permission: str) -> bool: ...


class SubcommandPermExtension(Extension):
    """
    用于简易检查调用者是否有命令权限的拓展。

    Example:
        >>> from nonebot_plugin_alconna.builtins.extensions.permission import SubcommandPermExtension
        >>>
        >>> matcher = on_alconna("...", extensions=[SubcommandPermExtension(...)])
    """

    @property
    def priority(self) -> int:
        return 20

    def __init__(self, checker: Checker, include_options: bool = False) -> None:
        """
        Args:
            checker: 权限检查函数，接受 bot、event、permission 三个参数，返回是否有权限的布尔值
            include_options: 是否需要选项的权限检查
        """
        self.checker = checker
        self.include_options = include_options

    @property
    def id(self) -> str:
        return "builtins.extensions.permission:SubcommandPermExtension"

    async def permission_check(self, bot: Bot, event: Event, medium: Arparma | CompSession) -> bool:
        if isinstance(medium, CompSession):
            return True
        base = [f"command.{medium.source.name}"]
        if self.include_options:
            base.extend(f"command.{medium.source.name}.$options.{opt}" for opt in medium.options)

        def gen_permissions(subcommands: dict[str, SubcommandResult], prefix: str):
            for name, result in subcommands.items():
                current_perm = f"{prefix}.{name}"
                yield current_perm
                if self.include_options and result.options:
                    for opt in result.options:
                        yield f"{current_perm}.$options.{opt}"
                if result.subcommands:
                    yield from gen_permissions(result.subcommands, current_perm)

        base.extend(gen_permissions(medium.subcommands, f"command.{medium.source.name}"))
        tasks = [self.checker(bot, event, perm) for perm in base]
        results = await asyncio.gather(*tasks)
        return all(results)


__extension__ = SubcommandPermExtension
