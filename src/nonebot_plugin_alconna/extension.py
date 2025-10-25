from __future__ import annotations

from abc import ABCMeta, abstractmethod
import asyncio
from contextlib import AsyncExitStack
from dataclasses import dataclass
import functools
import importlib as imp
import inspect
import re
from typing import TYPE_CHECKING, Any, ClassVar, Generic, Literal, TypeVar, Union, final, overload
from weakref import finalize

from arclet.alconna import Alconna, Arparma, CompSession
from nonebot import get_plugin_config
from nonebot.adapters import Bot, Event, Message
from nonebot.compat import PydanticUndefined
from nonebot.dependencies import Dependent, Param
from nonebot.internal.params import DependencyCache, DependParam, DependsInner
from nonebot.typing import T_State, _DependentCallable
from pydantic.fields import FieldInfo
from tarina import LRU, lang

from .config import Config
from .uniseg import UniMessage, get_message_id

OutputType = Literal["help", "shortcut", "completion", "error"]
T = TypeVar("T")
TM = TypeVar("TM", bound=Union[str, Message, UniMessage])
TE = TypeVar("TE", bound=Event)

if TYPE_CHECKING:
    from .rule import AlconnaRule


@dataclass
class Interface(Generic[TE]):
    event: TE
    state: T_State
    name: str
    annotation: Any
    default: Any


try:
    cache_msg = get_plugin_config(Config).alconna_cache_message
except ValueError:
    cache_msg = True


class Extension(metaclass=ABCMeta):
    _overrides: dict[str, bool]

    def __init_subclass__(cls, **kwargs):
        cls._overrides = {
            "message_provider": cls.message_provider != Extension.message_provider,
            "output_converter": cls.output_converter != Extension.output_converter,
            "send_wrapper": cls.send_wrapper != Extension.send_wrapper,
            "receive_wrapper": cls.receive_wrapper != Extension.receive_wrapper,
            "permission_check": cls.permission_check != Extension.permission_check,
            "context_provider": cls.context_provider != Extension.context_provider,
            "parse_wrapper": cls.parse_wrapper != Extension.parse_wrapper,
            "catch": cls.catch != Extension.catch and cls.before_catch != Extension.before_catch,
        }

    executor: ExtensionExecutor

    @property
    @abstractmethod
    def priority(self) -> int:
        """插件优先级。"""
        raise NotImplementedError

    @property
    @abstractmethod
    def id(self) -> str:
        """插件 ID。"""
        raise NotImplementedError

    @property
    def namespace(self) -> str:
        """插件所属命名空间"""
        return ""

    def validate(self, bot: Bot, event: Event) -> bool:
        return event.get_type() == "message"

    @overload
    async def inject(
        self, dependent: Dependent[T], *, use_cache: bool = True, validate: bool | FieldInfo = False
    ) -> T: ...

    @overload
    async def inject(self, dependent: tuple[str, type[T]]) -> T: ...

    @overload
    async def inject(self, dependent: Any) -> Any: ...

    @final
    async def inject(self, dependent: Any, use_cache: bool = True, validate: bool | FieldInfo = False) -> Any:
        # assert isinstance(dependent, (Dependent, DependsInner)), "仅支持 Dependent 或 DependsInner 类型的依赖注入"
        if isinstance(dependent, DependsInner):
            if not dependent.dependency:
                raise ValueError("DependsInner 未绑定任何依赖")
            use_cache = dependent.use_cache
            validate = dependent.validate
            dependent = Dependent.parse(call=dependent.dependency, allow_types=self.executor.params)
            param = DependParam(dependent=dependent, use_cache=use_cache, validate=validate)
        elif isinstance(dependent, Dependent):
            param = DependParam(dependent=dependent, use_cache=use_cache, validate=validate)
        else:
            for allow_type in self.executor.params:
                if param := allow_type._check_param(
                    inspect.Parameter(dependent[0], inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=dependent[1]),
                    self.executor.params,
                ):
                    break
            else:
                raise ValueError(f"Unknown parameter {dependent[0]} with type {dependent[1]}")
        return await self.executor._dependent_executor(param)

    async def output_converter(self, output_type: OutputType, content: str) -> UniMessage:
        """依据输出信息的类型，将字符串转换为消息对象以便发送。"""
        return UniMessage(content)

    async def message_provider(
        self, event: Event, state: T_State, bot: Bot, use_origin: bool = False
    ) -> UniMessage | None:
        """提供消息对象以便 Alconna 进行处理。"""
        return None

    async def receive_wrapper(self, bot: Bot, event: Event, command: Alconna, receive: UniMessage) -> UniMessage:
        """接收消息后的钩子函数。"""
        return receive

    async def permission_check(self, bot: Bot, event: Event, medium: Arparma | CompSession) -> bool:
        """命令首次解析并确认头部匹配（即确认选择响应）时对发送者的权限判断"""
        return True

    async def context_provider(self, ctx: dict[str, Any], event: Event, bot: Bot, state: T_State) -> dict[str, Any]:
        """提供上下文以便 Alconna 进行处理。"""
        return ctx

    async def parse_wrapper(self, bot: Bot, state: T_State, event: Event, res: Arparma) -> None:
        """解析消息后的钩子函数。"""
        return

    async def send_wrapper(self, bot: Bot, event: Event, send: TM) -> TM:
        """发送消息前的钩子函数。"""
        return send

    def before_catch(self, name: str, annotation: Any, default: Any) -> bool:
        """依赖注入的绑定确认函数。"""
        raise NotImplementedError

    async def catch(self, interface: Interface) -> Any:
        """自定义依赖注入处理函数。"""
        raise NotImplementedError

    def post_init(self, alc: Alconna) -> None:
        """Alconna 初始化后的钩子函数。"""
        return


class DefaultExtension(Extension):
    @property
    def priority(self) -> int:
        return 16

    @property
    def id(self) -> str:
        return "!default"


_callbacks = set()

unimsg_cache: LRU[str, UniMessage] = LRU(16)
unimsg_origin_cache: LRU[str, UniMessage] = LRU(16)


@dataclass
class SelectedExtensions:
    context: list[Extension]

    async def message_provider(
        self, event: Event, state: T_State, bot: Bot, use_origin: bool = False
    ) -> UniMessage | None:
        exc = None
        for ext in self.context:
            if not ext._overrides["message_provider"]:
                continue
            try:
                if (msg1 := await ext.message_provider(event, state, bot, use_origin)) is not None:
                    return msg1
            except Exception as e:
                exc = e
        if exc is not None:
            raise exc
        if event.get_type() == "message":
            msg_id = get_message_id(event, bot)
            if use_origin and cache_msg and (uni_msg := unimsg_origin_cache.get(msg_id)) is not None:
                return uni_msg
            if cache_msg and (uni_msg := unimsg_cache.get(msg_id)) is not None:
                return uni_msg
            msg = event.get_message()
            uni_msg = UniMessage.of(message=msg, bot=bot)
            unimsg_cache[msg_id] = uni_msg
            if (ori_msg := getattr(event, "original_message", None)) is not None:
                ori_uni_msg = await UniMessage.of(message=ori_msg, bot=bot).attach_reply(event=event, bot=bot)
                unimsg_origin_cache[msg_id] = ori_uni_msg
                if use_origin:
                    return ori_uni_msg
            return uni_msg
        return None

    async def receive_wrapper(self, bot: Bot, event: Event, command: Alconna, receive: UniMessage) -> UniMessage:
        res = receive
        for ext in self.context:
            if ext._overrides["receive_wrapper"]:
                res = await ext.receive_wrapper(bot, event, command, res)
        return res

    async def permission_check(self, bot: Bot, event: Event, medium: Arparma | CompSession) -> bool:
        for ext in self.context:
            if ext._overrides["permission_check"]:
                if await ext.permission_check(bot, event, medium) is False:
                    return False
                continue
        return True

    async def context_provider(self, event: Event, bot: Bot, state: T_State) -> dict[str, Any]:
        ctx = {}
        for ext in self.context:
            if ext._overrides["context_provider"]:
                ctx = await ext.context_provider(ctx, event, bot, state)
        ctx["event"] = event
        ctx["bot.self_id"] = bot.self_id
        if (platform := hasattr("bot", "platform")) and isinstance(platform, str):
            ctx["bot.platform"] = platform
        ctx["adapter.name"] = bot.adapter.get_name()
        return ctx

    async def parse_wrapper(self, bot: Bot, state: T_State, event: Event, res: Arparma) -> None:
        await asyncio.gather(
            *(ext.parse_wrapper(bot, state, event, res) for ext in self.context if ext._overrides["parse_wrapper"])
        )

    async def output_converter(self, output_type: OutputType, content: str) -> UniMessage:
        exc = None
        for ext in self.context:
            if not ext._overrides["output_converter"]:
                continue
            try:
                return await ext.output_converter(output_type, content)
            except Exception as e:
                exc = e
        if not exc:
            return UniMessage()
        raise exc  # type: ignore

    async def send_wrapper(self, bot: Bot, event: Event, send: TM) -> TM:
        res = send
        for ext in self.context:
            if ext._overrides["send_wrapper"]:
                res = await ext.send_wrapper(bot, event, res)
        return res


class _DependentExecutor:
    def __init__(
        self,
        bot: Bot,
        event: Event,
        state: T_State,
        stack: AsyncExitStack | None = None,
        dependency_cache: dict[_DependentCallable[Any], DependencyCache] | None = None,
    ):
        self.bot = bot
        self.event = event
        self.state = state
        self.stack = stack
        self.dependency_cache = dependency_cache or {}

    async def __call__(self, param: Param):
        return await param._solve(
            stack=self.stack, dependency_cache=self.dependency_cache, bot=self.bot, event=self.event, state=self.state
        )


class ExtensionExecutor(SelectedExtensions):
    globals: ClassVar[list[type[Extension] | Extension]] = [DefaultExtension()]
    _rule: AlconnaRule
    _dependent_executor: _DependentExecutor

    def __init__(
        self,
        rule: AlconnaRule,
        extensions: list[type[Extension] | Extension] | None = None,
        excludes: list[str | type[Extension]] | None = None,
    ):
        self.params: tuple[type[Param], ...] = ()
        self.extensions: list[Extension] = []
        for ext in self.globals:
            if isinstance(ext, type):
                self.extensions.append(ext())
            else:
                self.extensions.append(ext)
        for ext in extensions or []:
            if isinstance(ext, type):
                self.extensions.append(ext())
            else:
                self.extensions.append(ext)
        for exl in excludes or []:
            if isinstance(exl, str) and exl.startswith("!"):
                raise ValueError(lang.require("nbp-alc", "error.extension.forbid_exclude"))
        self._excludes = set(excludes or [])
        self.extensions = [
            ext
            for ext in self.extensions
            if ext.id not in self._excludes
            and ext.__class__ not in self._excludes
            and (not (ns := ext.namespace) or ns == rule._namespace)
        ]
        self.context = self.extensions
        self._rule = rule

        _callbacks.add(self._callback)

        finalize(self, _callbacks.discard, self._callback)

    def destroy(self) -> None:
        """销毁当前的扩展执行器，清理相关资源。"""
        _callbacks.discard(self._callback)
        self.extensions.clear()
        self.context.clear()
        del self._rule

    def _callback(self, *append_global_ext: type[Extension] | Extension):
        for _ext in append_global_ext:
            if isinstance(_ext, type):
                _ext = _ext()
            if _ext.id in self._excludes or _ext.__class__ in self._excludes:
                continue
            if (ns := _ext.namespace) and ns != self._rule._namespace:
                continue
            self.extensions.append(_ext)
            _ext.post_init(self._rule.command())  # type: ignore

    def select(self, bot: Bot, event: Event) -> SelectedExtensions:
        context = [ext for ext in self.extensions if ext.validate(bot, event)]
        context.sort(key=lambda ext: ext.priority)
        for ext in context:
            ext.executor = self
        return SelectedExtensions(context)

    def before_catch(self, name: str, annotation: Any, default: Any) -> bool:
        for ext in self.extensions:
            if ext._overrides["catch"]:
                if ext.before_catch(name, annotation, default):
                    return True
                continue
        return False

    async def catch(self, event: Event, state: T_State, name: str, annotation: Any, default: Any):
        for ext in self.extensions:
            if ext._overrides["catch"]:
                res = await ext.catch(Interface(event, state, name, annotation, default))
                if res is None:
                    continue
                return res
        return PydanticUndefined

    def post_init(self, command: Alconna) -> None:
        for ext in self.extensions:
            ext.post_init(command)


def add_global_extension(*ext: type[Extension] | Extension) -> None:
    ExtensionExecutor.globals.extend(ext)
    for callback in _callbacks:
        callback(*ext)


pattern = re.compile(r"(?P<module>[\w.]+)\s*" r"(:\s*(?P<attr>[\w.]+)\s*)?" r"((?P<extras>\[.*\])\s*)?$")


def load_from_path(path: str) -> None:
    if path.startswith("~."):
        path = f"nonebot_plugin_alconna{path[1:]}"
    elif path.startswith("~"):
        path = f"nonebot_plugin_alconna.{path[1:]}"
    elif path.startswith("@."):
        path = f"nonebot_plugin_alconna.builtins.extensions{path[1:]}"
    elif path.startswith("@"):
        path = f"nonebot_plugin_alconna.builtins.extensions.{path[1:]}"
    match = pattern.match(path)
    if not match:
        raise ValueError(lang.require("nbp-alc", "error.extension.path_invalid").format(path=path))
    module = imp.import_module(match.group("module"))
    attrs = filter(None, (match.group("attr") or "__extension__").split("."))
    ext = functools.reduce(getattr, attrs, module)
    if isinstance(ext, type) and issubclass(ext, Extension):
        add_global_extension(ext)  # type: ignore
    elif isinstance(ext, Extension):
        add_global_extension(ext)
    else:
        raise TypeError(lang.require("nbp-alc", "error.extension.path_load").format(path=path))
