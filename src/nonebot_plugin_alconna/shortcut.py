from __future__ import annotations

from pathlib import Path
from typing import Union, Callable
from collections.abc import Hashable
from datetime import datetime, timedelta

from nonebot.rule import Rule
from tarina import is_awaitable
from arclet.alconna import Alconna
from nonebot.permission import Permission
from nonebot.dependencies import Dependent
from arclet.alconna.tools import AlconnaString
from arclet.alconna.tools.construct import FuncMounter, MountConfig
from nonebot.compat import type_validate_json, type_validate_python
from nonebot.internal.adapter import Message, MessageSegment, MessageTemplate
from nonebot.typing import T_State, T_Handler, T_RuleChecker, T_PermissionChecker

from .typings import MReturn
from .util import annotation
from .pattern import patterns
from .extension import Extension
from .params import AlcExecResult
from .model import CompConfig, CommandModel
from .uniseg.fallback import FallbackStrategy
from .matcher import AlconnaMatcher, on_alconna
from .uniseg.template import UniMessageTemplate
from .uniseg import Segment, UniMessage, segment

_M = Union[str, Message, MessageSegment, MessageTemplate, Segment, UniMessage, UniMessageTemplate]


def funcommand(
    name: str | None = None,
    prefixes: list[str] | None = None,
    description: str | None = None,
    skip_for_unmatch: bool = True,
    auto_send_output: bool | None = None,
    extensions: list[type[Extension] | Extension] | None = None,
    exclude_ext: list[type[Extension] | str] | None = None,
    use_origin: bool | None = None,
    use_cmd_start: bool | None = None,
    use_cmd_sep: bool | None = None,
    response_self: bool | None = None,
    rule: Rule | T_RuleChecker | None = None,
    permission: Permission | T_PermissionChecker | None = None,
    *,
    handlers: list[T_Handler | Dependent] | None = None,
    temp: bool = False,
    expire_time: datetime | timedelta | None = None,
    priority: int = 1,
    block: bool = False,
    default_state: T_State | None = None,
    _depth: int = 0,
) -> Callable[[Callable[..., MReturn]], type[AlconnaMatcher]]:
    _config: MountConfig = {"raise_exception": False}
    if name:
        _config["command"] = name
    if prefixes:
        _config["prefixes"] = prefixes
    if description:
        _config["description"] = description

    def wrapper(func: Callable[..., MReturn]) -> type[AlconnaMatcher]:
        matcher = on_alconna(
            FuncMounter(func, _config),
            rule,
            skip_for_unmatch,
            auto_send_output,
            extensions=extensions,
            exclude_ext=exclude_ext,
            use_origin=use_origin,
            use_cmd_start=use_cmd_start,
            use_cmd_sep=use_cmd_sep,
            response_self=response_self,
            permission=permission,
            handlers=handlers,
            temp=temp,
            expire_time=expire_time,
            priority=priority,
            block=block,
            default_state=default_state,
            _depth=_depth + 1,
        )

        @matcher.handle()
        @annotation(results=AlcExecResult)
        async def handle_func(results: AlcExecResult):
            if res := results.get(func.__name__):
                if isinstance(res, Hashable) and is_awaitable(res):
                    res = await res
                if isinstance(res, (str, Message, MessageSegment, Segment, UniMessage, UniMessageTemplate)):
                    await matcher.send(res, fallback=True)

        return matcher

    return wrapper


class Command(AlconnaString):
    @staticmethod
    def args_gen(pattern: str, types: dict):
        return AlconnaString.args_gen(pattern, {**types, **patterns})

    def build(
        self,
        rule: Rule | T_RuleChecker | None = None,
        skip_for_unmatch: bool = True,
        auto_send_output: bool | None = None,
        aliases: set[str] | tuple[str, ...] | None = None,
        comp_config: CompConfig | None = None,
        extensions: list[type[Extension] | Extension] | None = None,
        exclude_ext: list[type[Extension] | str] | None = None,
        use_origin: bool | None = None,
        use_cmd_start: bool | None = None,
        use_cmd_sep: bool | None = None,
        response_self: bool | None = None,
        permission: Permission | T_PermissionChecker | None = None,
        *,
        handlers: list[T_Handler | Dependent] | None = None,
        temp: bool = False,
        expire_time: datetime | timedelta | None = None,
        priority: int = 1,
        block: bool = False,
        default_state: T_State | None = None,
        _depth: int = 0,
    ):
        params = locals().copy()
        params["_depth"] += 1
        params.pop("self")
        params.pop("__class__", None)
        ns = self.buffer.pop("namespace", None)
        alc = Alconna(*self.buffer.values(), *self.options, namespace=ns, meta=self.meta)
        for action in self.actions:
            alc.bind()(action)
        matcher = on_alconna(alc, **params)
        for key, args, kwargs in self.shortcuts:
            matcher.shortcut(key, args, **kwargs)  # type: ignore
        if self.actions:

            @matcher.handle()
            @annotation(results=AlcExecResult)
            async def handle_actions(results: AlcExecResult):
                for res in results.values():
                    if isinstance(res, Hashable) and is_awaitable(res):
                        res = await res
                    if isinstance(res, (str, Message, MessageSegment, Segment, UniMessage, UniMessageTemplate)):
                        await matcher.send(res, fallback=FallbackStrategy.rollback)

        return matcher

    @classmethod
    def from_model(cls, model: CommandModel):
        """从 `CommandModel` 生成 `Command` 对象"""
        cmd = cls(model.command, model.help)
        if model.usage:
            cmd.usage(model.usage)
        if model.examples:
            cmd.example("\n".join(model.examples))
        if model.author:
            cmd.meta.author = model.author
        if model.namespace:
            cmd.namespace(model.namespace)
        cmd.config(
            model.fuzzy_match,
            model.fuzzy_threshold,
            model.raise_exception,
            model.hide,
            model.hide_shortcut,
            model.keep_crlf,
            model.compact,
            model.strict,
            model.context_style,
            model.extra,
        )
        for opt in model.options:
            cmd.option(opt.name, opt.opt, opt.default)
        for sub in model.subcommands:
            cmd.subcommand(sub.name, sub.default)
        for alias in model.aliases:
            cmd.alias(alias)
        for short in model.shortcuts:
            cmd.shortcut(
                short.key,
                command=short.command,
                arguments=short.args,
                fuzzy=short.fuzzy,
                prefix=short.prefix,
                humanized=short.humanized,
            )
        if model.actions:
            _globals = {**segment.__dict__, **globals()}
            for act in model.actions:
                func = act.gen_exec(_globals)
                cmd.action(func)
        return cmd


def command_from_json(file: str | Path) -> Command:
    """从 JSON 文件中加载 Command 对象"""
    path = Path(file)
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8") as f:
        model = type_validate_json(CommandModel, f.read())
    return Command.from_model(model)


def command_from_yaml(file: str | Path) -> Command:
    """从 YAML 文件中加载 Command 对象

    使用该函数前请确保已安装 `pyyaml`
    """
    try:
        from yaml import safe_load
    except ImportError:
        raise ImportError("Please install pyyaml first") from None
    path = Path(file)
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8") as f:
        data = safe_load(f)
    model = type_validate_python(CommandModel, data)
    return Command.from_model(model)


def commands_from_json(file: str | Path) -> dict[str, Command]:
    """从单个 JSON 文件，或 JSON 文件目录中加载 Command 对象"""
    path = Path(file)
    if not path.exists():
        raise FileNotFoundError(path)
    if path.is_dir():
        return {(cmd := command_from_json(fl)).buffer["command"]: cmd for fl in path.iterdir()}
    with path.open("r", encoding="utf-8") as f:
        models = type_validate_json(list[CommandModel], f.read())
    return {model.command: Command.from_model(model) for model in models}


def commands_from_yaml(file: str | Path) -> dict[str, Command]:
    """从单个 YAML 文件，或 YAML 文件目录中加载 Command 对象

    使用该函数前请确保已安装 `pyyaml`

    在单个 YAML 文件下，若数据为列表，则直接解析为 CommandModel 列表；
        若数据为字典，则使用 values 解析为 CommandModel 列表
    """
    try:
        from yaml import safe_load
    except ImportError:
        raise ImportError("Please install pyyaml first") from None
    path = Path(file)
    if not path.exists():
        raise FileNotFoundError(path)
    if path.is_dir():
        return {(cmd := command_from_yaml(fl)).buffer["command"]: cmd for fl in path.iterdir()}
    with path.open("r", encoding="utf-8") as f:
        data = safe_load(f)
    if isinstance(data, list):
        models = type_validate_python(list[CommandModel], data)
    else:
        models = type_validate_python(list[CommandModel], list(data.values()))
    return {model.command: Command.from_model(model) for model in models}
