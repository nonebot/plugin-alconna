from __future__ import annotations

from typing import Callable

from nonebot.rule import Rule
from tarina import is_awaitable
from nonebot.matcher import Matcher
from nonebot.plugin.on import on_message
from nonebot.typing import T_RuleChecker
from arclet.alconna.tools import AlconnaFormat
from arclet.alconna import Alconna, command_manager
from arclet.alconna.tools.construct import FuncMounter
from nonebot.internal.adapter import Bot, Event, Message, MessageSegment

from .rule import alconna
from .model import CompConfig
from .typings import TConvert
from .params import AlcExecResult


def on_alconna(
    command: Alconna | str,
    rule: Rule | T_RuleChecker | None = None,
    skip_for_unmatch: bool = True,
    auto_send_output: bool = False,
    output_converter: TConvert | None = None,
    aliases: set[str | tuple[str, ...]] | None = None,
    comp_config: CompConfig | None = None,
    *args,
    _depth: int = 0,
    **kwargs,
) -> type[Matcher]:
    """注册一个消息事件响应器，并且当消息由指定 Alconna 解析并传出有效结果时响应。

    参数:
        command: Alconna 命令
        rule: 事件响应规则
        skip_for_unmatch: 是否在解析失败时跳过
        auto_send_output: 是否自动发送输出信息并跳过
        output_converter: 输出信息字符串转换为 Message 方法
        aliases: 命令别名
        comp_config: 补全会话配置, 不传入则不启用补全会话
        permission: 事件响应权限
        handlers: 事件处理函数列表
        temp: 是否为临时事件响应器（仅执行一次）
        expire_time: 事件响应器最终有效时间点，过时即被删除
        priority: 事件响应器优先级
        block: 是否阻止事件向更低优先级传递
        state: 默认 state
    """
    if isinstance(command, str):
        command = AlconnaFormat(command)
    if aliases and command.command:
        command_manager.delete(command)
        aliases.add(str(command.command))
        command.command = "re:(" + "|".join(aliases) + ")"
        command._hash = command._calc_hash()
        command_manager.register(command)
    return on_message(
        alconna(
            command, skip_for_unmatch, auto_send_output, output_converter, comp_config
        )
        & rule,
        *args,
        **kwargs,
        _depth=_depth + 1,  # type: ignore
    )


def funcommand(
    name: str | None = None,
    prefixes: list[str] | None = None,
    description: str | None = None,
    rule: Rule | T_RuleChecker | None = None,
    *args,
    _depth: int = 0,
    **kwargs,
):
    _config = {"raise_exception": False}
    if name:
        _config["command"] = name
    if prefixes:
        _config["prefixes"] = prefixes
    if description:
        _config["description"] = description

    def wrapper(func: Callable) -> type[Matcher]:
        alc = FuncMounter(func, _config)  # type: ignore

        async def handle(bot: Bot, event: Event, results: AlcExecResult):
            if res := results.get(func.__name__):
                if is_awaitable(res):
                    res = await res
                if isinstance(res, (str, Message, MessageSegment)):
                    await bot.send(event, res)

        matcher = on_alconna(alc, rule, *args, **kwargs, _depth=_depth + 1)
        matcher.handle()(handle)

        return matcher

    return wrapper
