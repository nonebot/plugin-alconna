from __future__ import annotations

from arclet.alconna.core import Alconna, T_Duplication
from arclet.alconna.tools import AlconnaString
from nonebot.matcher import Matcher
from nonebot.plugin.on import on_message
from nonebot.rule import Rule
from nonebot.typing import T_RuleChecker

from .rule import alconna


def on_alconna(
    command: Alconna | str,
    rule: Rule | T_RuleChecker | None = None,
    duplication: type[T_Duplication] | None = None,
    skip_for_unmatch: bool = True,
    _depth: int = 0,
    **kwargs,
) -> type[Matcher]:
    """注册一个消息事件响应器，并且当消息由指定 Alconna 解析并传出有效结果时响应。

    参数:
        command: Alconna 命令
        rule: 事件响应规则
        duplication: 可选的 Duplication 类型
        skip_for_unmatch: 是否在解析失败时跳过
        permission: 事件响应权限
        handlers: 事件处理函数列表
        temp: 是否为临时事件响应器（仅执行一次）
        expire_time: 事件响应器最终有效时间点，过时即被删除
        priority: 事件响应器优先级
        block: 是否阻止事件向更低优先级传递
        state: 默认 state
    """
    if isinstance(command, str):
        command = AlconnaString(command)
    return on_message(alconna(command, duplication, skip_for_unmatch) & rule, **kwargs, _depth=_depth + 1)  # type: ignore
