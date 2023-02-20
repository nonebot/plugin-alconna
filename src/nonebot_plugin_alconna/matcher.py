from __future__ import annotations

from typing import Any, Callable, Awaitable

from arclet.alconna import Alconna, Arparma
from arclet.alconna.tools import AlconnaString
from nonebot.matcher import Matcher
from nonebot.adapters import Message
from nonebot.plugin.on import on_message
from nonebot.rule import Rule
from nonebot.typing import T_RuleChecker

from .rule import alconna


def match_path(path: str):
    """
    当 Arpamar 解析成功后, 依据 path 是否存在以继续执行事件处理

    当 path 为 ‘$main’ 时表示认定当且仅当主命令匹配
    """

    def wrapper(result: Arparma):
        if path == "$main":
            return not result.components
        else:
            return result.query(path, "\0") != "\0"

    return wrapper


def match_value(path: str, value: Any, or_not: bool = False):
    """
    当 Arpamar 解析成功后, 依据查询 path 得到的结果是否符合传入的值以继续执行事件处理

    当 or_not 为真时允许查询 path 失败时继续执行事件处理
    """

    def wrapper(result: Arparma):
        if result.query(path, "\0") == value:
            return True
        return or_not and result.query(path, "\0") == "\0"

    return wrapper


_seminal = type("_seminal", (object,), {})


def assign(
    path: str, value: Any = _seminal, or_not: bool = False
) -> Callable[[Arparma], bool]:
    if value != _seminal:
        return match_value(path, value, or_not)
    if or_not:
        return lambda x: match_path("$main") or match_path(path)  # type: ignore
    return match_path(path)


def on_alconna(
    command: Alconna | str,
    *checker: Callable[[Arparma], bool],
    rule: Rule | T_RuleChecker | None = None,
    skip_for_unmatch: bool = True,
    auto_send_output: bool = False,
    output_converter: Callable[[str], Message | Awaitable[Message]] | None = None,
    _depth: int = 0,
    **kwargs,
) -> type[Matcher]:
    """注册一个消息事件响应器，并且当消息由指定 Alconna 解析并传出有效结果时响应。

    参数:
        command: Alconna 命令
        checker: Arparma 检查器，会在解析后使用
        rule: 事件响应规则
        skip_for_unmatch: 是否在解析失败时跳过
        auto_send_output: 是否自动发送输出信息并跳过
        output_converter: 输出信息字符串转换为 Message 方法
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
    return on_message(
        alconna(
            command,
            *checker,
            skip_for_unmatch=skip_for_unmatch,
            auto_send_output=auto_send_output,
            output_converter=output_converter
        ) & rule,
        **kwargs,
        _depth=_depth + 1  # type: ignore
    )
