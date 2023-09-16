from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Union, Callable, ClassVar, Iterable, NoReturn, Protocol

from nonebot.rule import Rule
from nonebot.params import Depends
from nonebot.permission import Permission
from nonebot.dependencies import Dependent
from nepattern import STRING, AnyOne, AnyString
from nonebot.consts import ARG_KEY, RECEIVE_KEY
from tarina import is_awaitable, run_always_await
from arclet.alconna.tools import AlconnaFormat, AlconnaString
from arclet.alconna.tools.construct import FuncMounter, MountConfig
from arclet.alconna import Arg, Args, Alconna, ShortcutArgs, command_manager
from nonebot.matcher import Matcher, current_bot, current_event, current_matcher
from nonebot.typing import T_State, T_Handler, T_RuleChecker, T_PermissionChecker
from nonebot.exception import PausedException, FinishedException, RejectedException
from nonebot.plugin.on import store_matcher, get_matcher_module, get_matcher_plugin
from nonebot.internal.adapter import (
    Bot,
    Event,
    Message,
    MessageSegment,
    MessageTemplate,
)

from .rule import alconna
from .model import CompConfig
from .consts import ALCONNA_ARG_KEY
from .typings import MReturn, TConvert
from .uniseg import Segment, UniMessage
from .params import MIDDLEWARE, Check, AlcExecResult, assign, _seminal, _Dispatch

_M = Union[str, Message, MessageSegment, MessageTemplate, Segment, UniMessage]


class ArgsMounter(Protocol):
    args: Args


def extract_arg(path: str, target: ArgsMounter) -> Arg | None:
    """从 Alconna 中提取参数"""
    parts = path.split(".")
    if len(parts) == 1:
        return next((arg for arg in target.args.argument if arg.name == path), None)
    _parts, end = parts[:-1], parts[-1]
    if not (options := getattr(target, "options", None)):
        return
    for opt in options:
        if opt.dest == _parts[0]:
            return extract_arg(".".join(_parts[1:] + [end]), opt)
    return


def _validate(target: Arg[Any], arg: MessageSegment):
    value = target.value
    if value == AnyOne:
        return arg
    if value == AnyString or (value == STRING and arg.is_text()):
        return str(arg)
    default_val = target.field.default
    res = (
        value.invalidate(arg, default_val)
        if value.anti
        else value.validate(arg, default_val)
    )
    if target.optional and res.flag != "valid":
        return
    if res.flag == "error":
        return
    return res._value  # noqa


class AlconnaMatcher(Matcher):
    command: ClassVar[Alconna]

    @classmethod
    def shortcut(cls, key: str, args: ShortcutArgs | None = None, delete: bool = False):
        return cls.command.shortcut(key, args, delete)

    @classmethod
    def assign(
        cls,
        path: str,
        value: Any = _seminal,
        or_not: bool = False,
        parameterless: Iterable[Any] | None = None,
    ) -> Callable[[T_Handler], T_Handler]:
        """装饰一个函数来向事件响应器直接添加一个处理函数

        此装饰是 @handle([Check(assign(...))]) 的快捷写法

        参数:
            path: 指定的查询路径, "$main" 表示没有任何选项/子命令匹配的时候
            value: 可能的指定查询值
            or_not: 是否同时处理没有查询成功的情况
            parameterless: 非参数类型依赖列表
        """
        parameterless = [Check(assign(path, value, or_not)), *(parameterless or [])]

        def _decorator(func: T_Handler) -> T_Handler:
            cls.append_handler(func, parameterless=parameterless)
            return func

        return _decorator

    def set_path_arg(self, path: str, content: Any) -> None:
        """设置一个 `got_path` 内容"""
        self.state[ALCONNA_ARG_KEY.format(key=path)] = content

    def get_path_arg(self, path: str, default: Any) -> Any:
        """获取一个 `got_path` 内容"""
        return self.state.get(ALCONNA_ARG_KEY.format(key=path), default)

    @classmethod
    def got_path(
        cls,
        path: str,
        prompt: _M | None = None,
        middleware: MIDDLEWARE | None = None,
        parameterless: Iterable[Any] | None = None,
    ) -> Callable[[T_Handler], T_Handler]:
        """装饰一个函数来指示 NoneBot 获取一个路径下的参数 `path`

        当要获取的 `path` 不存在时接收用户新的一条消息再运行该函数

        如果 `path` 已存在则直接继续运行

        本插件会获取消息的最后一个消息段并转为 path 对应的类型

        参数:
            path: 参数路径名
            prompt: 在参数不存在时向用户发送的消息，支持 `UniMessage`
            parameterless: 非参数类型依赖列表
        """
        if not (arg := extract_arg(path, cls.command)):
            raise ValueError(f"Path {path} not found in Alconna")

        async def _key_getter(event: Event, bot: Bot, matcher: AlconnaMatcher):
            matcher.set_target(ALCONNA_ARG_KEY.format(key=path))
            if matcher.get_target() == ALCONNA_ARG_KEY.format(key=path):
                ms = event.get_message()[-1]
                if (
                    ms.is_text()
                    and not ms.data["text"].strip()
                    and len(event.get_message()) > 1
                ):
                    ms = event.get_message()[-2]
                if (res := _validate(arg, ms)) is None:  # type: ignore
                    await matcher.reject(prompt, fallback=True)
                    return
                if middleware:
                    res = await run_always_await(middleware, bot, matcher.state, res)
                matcher.set_path_arg(path, res)
                return
            if matcher.state.get(ALCONNA_ARG_KEY.format(key=path), ...) is not ...:
                return
            await matcher.reject(prompt, fallback=True)

        _parameterless = (*(parameterless or ()), Depends(_key_getter))

        def _decorator(func: T_Handler) -> T_Handler:
            if cls.handlers and cls.handlers[-1].call is func:
                func_handler = cls.handlers[-1]
                new_handler = Dependent(
                    call=func_handler.call,
                    params=func_handler.params,
                    parameterless=Dependent.parse_parameterless(
                        tuple(_parameterless), cls.HANDLER_PARAM_TYPES
                    )
                    + func_handler.parameterless,
                )
                cls.handlers[-1] = new_handler
            else:
                cls.append_handler(func, parameterless=_parameterless)

            return func

        return _decorator

    @classmethod
    async def reject_path(
        cls,
        path: str,
        prompt: _M | None = None,
        fallback: bool = False,
        **kwargs,
    ) -> NoReturn:
        """最近使用 `got_path` 接收的消息不符合预期，
        发送一条消息给当前交互用户并将当前事件处理流程中断在当前位置，在接收用户新的一条消息后从头开始执行当前处理函数

        参数:
            path: 参数路径名
            prompt: 消息内容, 支持 `UniMessage`
            fallback: 若 UniMessage 中的元素无法被解析为当前 adapter 的消息元素时，
                是否转为字符串
            kwargs: {ref}`nonebot.adapters.Bot.send` 的参数，
                请参考对应 adapter 的 bot 对象 api
        """
        matcher = current_matcher.get()
        matcher.set_target(ALCONNA_ARG_KEY.format(key=path))
        if prompt is not None:
            await cls.send(prompt, fallback=fallback, **kwargs)
        raise RejectedException

    @classmethod
    def dispatch(
        cls,
        path: str,
        value: Any = _seminal,
        or_not: bool = False,
        rule: Rule | T_RuleChecker | None = None,
        permission: Permission | T_PermissionChecker | None = None,
        *,
        handlers: list[T_Handler | Dependent] | None = None,
        temp: bool = False,
        expire_time: datetime | timedelta | None = None,
        priority: int = 1,
        block: bool = False,
        state: T_State | None = None,
        _depth: int = 0,
    ) -> type[AlconnaMatcher]:
        """注册一个消息事件响应器，
        并且当消息由指定 Alconna 解析并且结果符合 assign 预期时执行

        参数:
            path: 指定的查询路径, "$main" 表示没有任何选项/子命令匹配的时候
            value: 可能的指定查询值
            or_not: 是否同时处理没有查询成功的情况
            rule: 事件响应规则
            permission: 事件响应权限
            handlers: 事件处理函数列表
            temp: 是否为临时事件响应器（仅执行一次）
            expire_time: 事件响应器最终有效时间点，过时即被删除
            priority: 事件响应器优先级，其会基于父级事件响应器的优先级进行累加
            block: 是否阻止事件向更低优先级传递
            state: 默认 state
        """

        fn = _Dispatch(path, value, or_not)
        cls.handle()(fn.set)

        matcher: type[AlconnaMatcher] = AlconnaMatcher.new(
            "message",
            rule & Rule(fn),
            Permission() | permission,
            temp=temp,
            expire_time=expire_time,
            priority=cls.priority + priority,
            block=block,
            handlers=handlers,
            plugin=get_matcher_plugin(_depth + 1),
            module=get_matcher_module(_depth + 1),
            default_state=state,
        )
        store_matcher(matcher)
        matcher.command = cls.command
        return matcher

    @classmethod
    def got(
        cls,
        key: str,
        prompt: _M | None = None,
        parameterless: Iterable[Any] | None = None,
    ) -> Callable[[T_Handler], T_Handler]:
        """装饰一个函数来指示 NoneBot 获取一个参数 `key`

        当要获取的 `key` 不存在时接收用户新的一条消息再运行该函数，
        如果 `key` 已存在则直接继续运行

        参数:
            key: 参数名
            prompt: 在参数不存在时向用户发送的消息, 支持 `UniMessage`
            parameterless: 非参数类型依赖列表
        """

        async def _key_getter(event: Event, matcher: AlconnaMatcher):
            matcher.set_target(ARG_KEY.format(key=key))
            if matcher.get_target() == ARG_KEY.format(key=key):
                matcher.set_arg(key, event.get_message())
                return
            if matcher.get_arg(key, ...) is not ...:
                return
            await matcher.reject(prompt, fallback=True)

        _parameterless = (Depends(_key_getter), *(parameterless or ()))

        def _decorator(func: T_Handler) -> T_Handler:
            if cls.handlers and cls.handlers[-1].call is func:
                func_handler = cls.handlers[-1]
                new_handler = Dependent(
                    call=func_handler.call,
                    params=func_handler.params,
                    parameterless=Dependent.parse_parameterless(
                        tuple(_parameterless), cls.HANDLER_PARAM_TYPES
                    )
                    + func_handler.parameterless,
                )
                cls.handlers[-1] = new_handler
            else:
                cls.append_handler(func, parameterless=_parameterless)

            return func

        return _decorator

    @classmethod
    async def send(
        cls,
        message: _M,
        fallback: bool = False,
        **kwargs: Any,
    ) -> Any:
        """发送一条消息给当前交互用户

        `AlconnaMatcher` 下增加了对 UniMessage 的发送支持

        参数:
            message: 消息内容, 支持 `UniMessage`
            fallback: 若 UniMessage 中的元素无法被解析为当前 adapter 的消息元素时，
                是否转为字符串
            kwargs: {ref}`nonebot.adapters.Bot.send` 的参数，
                请参考对应 adapter 的 bot 对象 api
        """
        bot = current_bot.get()
        event = current_event.get()
        state = current_matcher.get().state
        if isinstance(message, MessageTemplate):
            _message = message.format(**state)
        elif isinstance(message, Segment):
            _message = UniMessage(message)
        else:
            _message = message
        if isinstance(_message, UniMessage):
            _message = await _message.export(bot, fallback)
        return await bot.send(event=event, message=_message, **kwargs)

    @classmethod
    async def finish(
        cls,
        message: _M | None = None,
        fallback: bool = False,
        **kwargs,
    ) -> NoReturn:
        """发送一条消息给当前交互用户并结束当前事件响应器

        参数:
            message: 消息内容, 支持 `UniMessage`
            fallback: 若 UniMessage 中的元素无法被解析为当前 adapter 的消息元素时，
                是否转为字符串
            kwargs: {ref}`nonebot.adapters.Bot.send` 的参数，
                请参考对应 adapter 的 bot 对象 api
        """
        if message is not None:
            await cls.send(message, fallback=fallback, **kwargs)
        raise FinishedException

    @classmethod
    async def pause(
        cls,
        prompt: _M | None = None,
        fallback: bool = False,
        **kwargs,
    ) -> NoReturn:
        """发送一条消息给当前交互用户并暂停事件响应器，在接收用户新的一条消息后继续下一个处理函数

        参数:
            prompt: 消息内容, 支持 `UniMessage`
            fallback: 若 UniMessage 中的元素无法被解析为当前 adapter 的消息元素时，
                是否转为字符串
            kwargs: {ref}`nonebot.adapters.Bot.send` 的参数，
                请参考对应 adapter 的 bot 对象 api
        """
        if prompt is not None:
            await cls.send(prompt, fallback=fallback, **kwargs)
        raise PausedException

    @classmethod
    async def reject(
        cls,
        prompt: _M | None = None,
        fallback: bool = False,
        **kwargs,
    ) -> NoReturn:
        """最近使用 `got` / `receive` 接收的消息不符合预期，
        发送一条消息给当前交互用户并将当前事件处理流程中断在当前位置，在接收用户新的一个事件后从头开始执行当前处理函数

        参数:
            prompt: 消息内容, 支持 `UniMessage`
            fallback: 若 UniMessage 中的元素无法被解析为当前 adapter 的消息元素时，
                是否转为字符串
            kwargs: {ref}`nonebot.adapters.Bot.send` 的参数，
                请参考对应 adapter 的 bot 对象 api
        """
        if prompt is not None:
            await cls.send(prompt, fallback=fallback, **kwargs)
        raise RejectedException

    @classmethod
    async def reject_arg(
        cls,
        key: str,
        prompt: _M | None = None,
        fallback: bool = False,
        **kwargs,
    ) -> NoReturn:
        """最近使用 `got` 接收的消息不符合预期，
        发送一条消息给当前交互用户并将当前事件处理流程中断在当前位置，在接收用户新的一条消息后从头开始执行当前处理函数

        参数:
            key: 参数名
            prompt: 消息内容, 支持 `UniMessage`
            fallback: 若 UniMessage 中的元素无法被解析为当前 adapter 的消息元素时，
                是否转为字符串
            kwargs: {ref}`nonebot.adapters.Bot.send` 的参数，
                请参考对应 adapter 的 bot 对象 api
        """
        matcher = current_matcher.get()
        matcher.set_target(ARG_KEY.format(key=key))
        if prompt is not None:
            await cls.send(prompt, fallback=fallback, **kwargs)
        raise RejectedException

    @classmethod
    async def reject_receive(
        cls,
        id: str = "",
        prompt: _M | None = None,
        fallback: bool = False,
        **kwargs,
    ) -> NoReturn:
        """最近使用 `receive` 接收的消息不符合预期，
        发送一条消息给当前交互用户并将当前事件处理流程中断在当前位置，在接收用户新的一个事件后从头开始执行当前处理函数

        参数:
            id: 消息 id
            prompt: 消息内容, 支持 `UniMessage`
            fallback: 若 UniMessage 中的元素无法被解析为当前 adapter 的消息元素时，
                是否转为字符串
            kwargs: {ref}`nonebot.adapters.Bot.send` 的参数，
                请参考对应 adapter 的 bot 对象 api
        """
        matcher = current_matcher.get()
        matcher.set_target(RECEIVE_KEY.format(id=id))
        if prompt is not None:
            await cls.send(prompt, fallback=fallback, **kwargs)
        raise RejectedException


def on_alconna(
    command: Alconna | str,
    rule: Rule | T_RuleChecker | None = None,
    skip_for_unmatch: bool = True,
    auto_send_output: bool = False,
    output_converter: TConvert | None = None,
    aliases: set[str] | tuple[str, ...] | None = None,
    comp_config: CompConfig | None = None,
    use_origin: bool = False,
    use_cmd_start: bool = False,
    use_cmd_sep: bool = False,
    permission: Permission | T_PermissionChecker | None = None,
    *,
    handlers: list[T_Handler | Dependent] | None = None,
    temp: bool = False,
    expire_time: datetime | timedelta | None = None,
    priority: int = 1,
    block: bool = False,
    state: T_State | None = None,
    _depth: int = 0,
) -> type[AlconnaMatcher]:
    """注册一个消息事件响应器，并且当消息由指定 Alconna 解析并传出有效结果时响应。

    参数:
        command: Alconna 命令
        rule: 事件响应规则
        skip_for_unmatch: 是否在解析失败时跳过
        auto_send_output: 是否自动发送输出信息并跳过
        output_converter: 输出信息字符串转换为 Message 方法
        aliases: 命令别名
        comp_config: 补全会话配置, 不传入则不启用补全会话
        use_origin: 是否使用未经 to_me 等处理过的消息
        use_cmd_start: 是否使用 nb 全局配置里的命令起始符
        use_cmd_sep: 是否使用 nb 全局配置里的命令分隔符
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
    if aliases:
        aliases = set(aliases)
        command_manager.delete(command)
        if command.command:
            aliases.add(str(command.command))
        command.command = "re:(" + "|".join(aliases) + ")"
        command._hash = command._calc_hash()
        command_manager.register(command)
    matcher: type[AlconnaMatcher] = AlconnaMatcher.new(
        "message",
        rule
        & alconna(
            command,
            skip_for_unmatch,
            auto_send_output,
            output_converter,
            comp_config,
            use_origin,
            use_cmd_start,
            use_cmd_sep,
        ),
        Permission() | permission,
        temp=temp,
        expire_time=expire_time,
        priority=priority,
        block=block,
        handlers=handlers,
        plugin=get_matcher_plugin(_depth + 1),
        module=get_matcher_module(_depth + 1),
        default_state=state,
    )
    store_matcher(matcher)
    matcher.command = command
    return matcher


def funcommand(
    name: str | None = None,
    prefixes: list[str] | None = None,
    description: str | None = None,
    skip_for_unmatch: bool = True,
    auto_send_output: bool = False,
    output_converter: TConvert | None = None,
    use_origin: bool = False,
    use_cmd_start: bool = False,
    use_cmd_sep: bool = False,
    rule: Rule | T_RuleChecker | None = None,
    permission: Permission | T_PermissionChecker | None = None,
    *,
    handlers: list[T_Handler | Dependent] | None = None,
    temp: bool = False,
    expire_time: datetime | timedelta | None = None,
    priority: int = 1,
    block: bool = False,
    state: T_State | None = None,
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
            FuncMounter(func, _config),  # type: ignore
            rule,
            skip_for_unmatch,
            auto_send_output,
            output_converter,
            use_origin=use_origin,
            use_cmd_start=use_cmd_start,
            use_cmd_sep=use_cmd_sep,
            permission=permission,
            handlers=handlers,
            temp=temp,
            expire_time=expire_time,
            priority=priority,
            block=block,
            state=state,
            _depth=_depth + 1,
        )

        @matcher.handle()
        async def handle(results: AlcExecResult):
            if res := results.get(func.__name__):
                if is_awaitable(res):
                    res = await res
                if isinstance(res, (str, Message, MessageSegment, Segment, UniMessage)):
                    await matcher.send(res, fallback=True)

        return matcher

    return wrapper


class Command(AlconnaString):
    def build(
        self,
        rule: Rule | T_RuleChecker | None = None,
        skip_for_unmatch: bool = True,
        auto_send_output: bool = False,
        output_converter: TConvert | None = None,
        aliases: set[str] | tuple[str, ...] | None = None,
        comp_config: CompConfig | None = None,
        use_origin: bool = False,
        use_cmd_start: bool = False,
        use_cmd_sep: bool = False,
        permission: Permission | T_PermissionChecker | None = None,
        *,
        handlers: list[T_Handler | Dependent] | None = None,
        temp: bool = False,
        expire_time: datetime | timedelta | None = None,
        priority: int = 1,
        block: bool = False,
        state: T_State | None = None,
        _depth: int = 0,
    ):
        params = locals().copy()
        params["_depth"] += 1
        params.pop("self")
        params.pop("__class__")
        alc = super().build()
        return on_alconna(alc, **params)
