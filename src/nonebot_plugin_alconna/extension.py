from __future__ import annotations

import re
import asyncio
import functools
import importlib as imp
from weakref import finalize
from dataclasses import dataclass
from typing_extensions import Self
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any, Union, Generic, Literal, TypeVar

from tarina import lang
from nonebot.typing import T_State
from arclet.alconna import Alconna, Arparma
from nonebot.compat import PydanticUndefined
from nonebot.adapters import Bot, Event, Message

from .uniseg import UniMessage, FallbackMessage

OutputType = Literal["help", "shortcut", "completion", "error"]
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


class Extension(metaclass=ABCMeta):
    _overrides: dict[str, bool]

    def __init_subclass__(cls, **kwargs):
        cls._overrides = {
            "output_converter": cls.output_converter != Extension.output_converter,
            "send_wrapper": cls.send_wrapper != Extension.send_wrapper,
            "receive_wrapper": cls.receive_wrapper != Extension.receive_wrapper,
            "permission_check": cls.permission_check != Extension.permission_check,
            "context_provider": cls.context_provider != Extension.context_provider,
            "parse_wrapper": cls.parse_wrapper != Extension.parse_wrapper,
            "catch": cls.catch != Extension.catch and cls.before_catch != Extension.before_catch,
        }

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
        return True

    async def output_converter(self, output_type: OutputType, content: str) -> Message | UniMessage:
        """依据输出信息的类型，将字符串转换为消息对象以便发送。"""
        return FallbackMessage(content)

    async def message_provider(
        self, event: Event, state: T_State, bot: Bot, use_origin: bool = False
    ) -> Message | UniMessage | None:
        """提供消息对象以便 Alconna 进行处理。"""
        if event.get_type() != "message":
            return None
        msg: Message = event.get_message()
        if use_origin:
            try:
                msg: Message = getattr(event, "original_message", msg)  # type: ignore
            except (NotImplementedError, ValueError):
                return None
        return msg

    async def receive_wrapper(self, bot: Bot, event: Event, command: Alconna, receive: TM) -> TM:
        """接收消息后的钩子函数。"""
        return receive

    async def permission_check(self, bot: Bot, event: Event, command: Alconna) -> bool:
        """命令首次解析并确认头部匹配（即确认选择响应）时对发送者的权限判断"""
        return True

    async def context_provider(self, ctx: dict[str, Any], event: Event, bot: Bot, state: T_State) -> dict[str, Any]:
        """提供上下文以便 Alconna 进行处理。"""
        return ctx

    async def parse_wrapper(self, bot: Bot, state: T_State, event: Event, res: Arparma) -> None:
        """解析消息后的钩子函数。"""
        ...

    async def send_wrapper(self, bot: Bot, event: Event, send: TM) -> TM:
        """发送消息前的钩子函数。"""
        return send

    def before_catch(self, name: str, annotation: Any, default: Any) -> bool:
        """依赖注入的绑定确认函数。"""
        ...

    async def catch(self, interface: Interface) -> Any:
        """自定义依赖注入处理函数。"""
        ...

    def post_init(self, alc: Alconna) -> None:
        """Alconna 初始化后的钩子函数。"""
        ...


class DefaultExtension(Extension):
    @property
    def priority(self) -> int:
        return 16

    @property
    def id(self) -> str:
        return "!default"


_callbacks = set()


class ExtensionExecutor:
    globals: list[type[Extension] | Extension] = [DefaultExtension()]
    _rule: AlconnaRule

    def __init__(
        self,
        rule: AlconnaRule,
        extensions: list[type[Extension] | Extension] | None = None,
        excludes: list[str | type[Extension]] | None = None,
    ):
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
                raise ValueError(lang.require("nbp-alc", "error.extension_forbid_exclude"))
        self._excludes = set(excludes or [])
        self.extensions = [
            ext
            for ext in self.extensions
            if ext.id not in self._excludes
            and ext.__class__ not in self._excludes
            and (not (ns := ext.namespace) or ns == rule.command.namespace)
        ]
        self.context: list[Extension] = []
        self._rule = rule

        _callbacks.add(self._callback)

        finalize(self, _callbacks.remove, self._callback)

    def _callback(self, *append_global_ext: type[Extension] | Extension):
        for _ext in append_global_ext:
            if isinstance(_ext, type):
                _ext = _ext()
            if _ext.id in self._excludes or _ext.__class__ in self._excludes:
                continue
            if (ns := _ext.namespace) and ns != self._rule.command.namespace:
                continue
            self.extensions.append(_ext)
            _ext.post_init(self._rule.command)

    def __exit__(self, exc_type, exc_value, traceback):
        self.context.clear()

    def select(self, bot: Bot, event: Event) -> Self:
        self.context = [ext for ext in self.extensions if ext.validate(bot, event)]
        self.context.sort(key=lambda ext: ext.priority)
        return self

    async def output_converter(self, output_type: OutputType, content: str) -> Message | UniMessage:
        exc = None
        for ext in self.context:
            if not ext._overrides["output_converter"]:
                continue
            try:
                return await ext.output_converter(output_type, content)
            except Exception as e:
                exc = e
        if not exc:
            return FallbackMessage()
        raise exc  # type: ignore

    async def message_provider(
        self, event: Event, state: T_State, bot: Bot, use_origin: bool = False
    ) -> Message | UniMessage | None:
        exc = None
        for ext in self.context:
            try:
                if (msg := await ext.message_provider(event, state, bot, use_origin)) is not None:
                    return msg
            except Exception as e:
                exc = e
        if exc is not None:
            raise exc

        return None

    async def receive_wrapper(self, bot: Bot, event: Event, receive: TM) -> TM:
        res = receive
        for ext in self.context:
            if ext._overrides["receive_wrapper"]:
                res = await ext.receive_wrapper(bot, event, self._rule.command, res)
        return res

    async def permission_check(self, bot: Bot, event: Event) -> bool:
        for ext in self.context:
            if ext._overrides["permission_check"]:
                if await ext.permission_check(bot, event, self._rule.command) is False:
                    return False
                continue
        return True

    async def context_provider(self, event: Event, bot: Bot, state: T_State) -> dict[str, Any]:
        ctx = {}
        for ext in self.context:
            if ext._overrides["context_provider"]:
                ctx = await ext.context_provider(ctx, event, bot, state)
        ctx["event"] = event
        # ctx["bot"] = bot
        return ctx

    async def parse_wrapper(self, bot: Bot, state: T_State, event: Event, res: Arparma) -> None:
        await asyncio.gather(
            *(ext.parse_wrapper(bot, state, event, res) for ext in self.context if ext._overrides["parse_wrapper"])
        )

    async def send_wrapper(self, bot: Bot, event: Event, send: TM) -> TM:
        res = send
        for ext in self.context:
            if ext._overrides["send_wrapper"]:
                res = await ext.send_wrapper(bot, event, res)
        return res

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

    def post_init(self) -> None:
        for ext in self.extensions:
            ext.post_init(self._rule.command)


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
        raise ValueError(lang.require("nbp-alc", "error.extension_path_invalid").format(path=path))
    module = imp.import_module(match.group("module"))
    attrs = filter(None, (match.group("attr") or "__extension__").split("."))
    ext = functools.reduce(getattr, attrs, module)
    if isinstance(ext, type) and issubclass(ext, Extension):
        add_global_extension(ext)
    elif isinstance(ext, Extension):
        add_global_extension(ext)
    else:
        raise TypeError(lang.require("nbp-alc", "error.extension_path_load").format(path=path))
