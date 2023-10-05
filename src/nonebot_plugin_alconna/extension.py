from __future__ import annotations

import re
import asyncio
import functools
import importlib as imp
from typing_extensions import Self
from typing import Literal, TypeVar
from abc import ABCMeta, abstractmethod

from tarina import lang
from nonebot.typing import T_State
from arclet.alconna import Alconna, Arparma
from nonebot.adapters import Bot, Event, Message

from .uniseg import UniMessage, FallbackMessage

OutputType = Literal["help", "shortcut", "completion"]
TM = TypeVar("TM", Message, UniMessage)


class Extension(metaclass=ABCMeta):
    _overrides: dict[str, bool]

    def __init_subclass__(cls, **kwargs):
        cls._overrides = {
            "send_wrapper": cls.send_wrapper == Extension.send_wrapper,
            "receive_wrapper": cls.receive_wrapper == Extension.receive_wrapper,
            "parse_wrapper": cls.parse_wrapper == Extension.parse_wrapper,
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

    async def receive_wrapper(self, bot: Bot, event: Event, receive: TM) -> TM:
        """接收消息后的钩子函数。"""
        return receive

    async def parse_wrapper(self, bot: Bot, state: T_State, event: Event, res: Arparma) -> None:
        """解析消息后的钩子函数。"""
        pass

    async def send_wrapper(self, bot: Bot, event: Event, send: TM) -> TM:
        """发送消息前的钩子函数。"""
        return send

    def post_init(self, alc: Alconna) -> None:
        """Alconna 初始化后的钩子函数。"""
        pass


class DefaultExtension(Extension):
    @property
    def priority(self) -> int:
        return 16

    @property
    def id(self) -> str:
        return "!default"


class ExtensionExecutor:
    globals: list[type[Extension] | Extension] = [DefaultExtension()]

    def __init__(
        self,
        extensions: list[type[Extension] | Extension] | None = None,
        excludes: list[str | type[Extension]] | None = None,
    ):
        self.extensions: list[Extension] = []
        for ext in self.globals:
            if isinstance(ext, type):
                self.extensions.append(ext())
            else:
                self.extensions.append(ext)
        if extensions:
            for ext in extensions:
                if isinstance(ext, type):
                    self.extensions.append(ext())
                else:
                    self.extensions.append(ext)
        if excludes:
            for ext in excludes:
                if isinstance(ext, str):
                    if ext.startswith("!"):
                        raise ValueError(lang.require("nbp-alc", "error.extension_forbid_exclude"))
                    self.extensions = [ext for ext in self.extensions if ext.id != ext]
                else:
                    self.extensions = [ext for ext in self.extensions if not isinstance(ext, ext)]
        self.context: list[Extension] = []

    def __exit__(self, exc_type, exc_value, traceback):
        self.context.clear()

    def select(self, bot: Bot, event: Event) -> Self:
        self.context = [ext for ext in self.extensions if ext.validate(bot, event)]
        self.context.sort(key=lambda ext: ext.priority)
        return self

    async def output_converter(self, output_type: OutputType, content: str) -> Message | UniMessage:
        exc = None
        for ext in self.context:
            try:
                return await ext.output_converter(output_type, content)
            except Exception as e:
                exc = e
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
                res = await ext.receive_wrapper(bot, event, res)
        return res

    async def parse_wrapper(self, bot: Bot, state: T_State, event: Event, res: Arparma) -> None:
        await asyncio.gather(
            *(
                ext.parse_wrapper(bot, state, event, res)
                for ext in self.context
                if ext._overrides["parse_wrapper"]
            )
        )

    async def send_wrapper(self, bot: Bot, event: Event, send: TM) -> TM:
        res = send
        for ext in self.context:
            if ext._overrides["send_wrapper"]:
                res = await ext.send_wrapper(bot, event, res)
        return res

    def post_init(self, alc: Alconna) -> None:
        for ext in self.extensions:
            ext.post_init(alc)


def add_global_extension(*ext: type[Extension] | Extension) -> None:
    ExtensionExecutor.globals.extend(ext)


pattern = re.compile(r"(?P<module>[\w.]+)\s*" r"(:\s*(?P<attr>[\w.]+)\s*)?" r"((?P<extras>\[.*\])\s*)?$")


def load_from_path(path: str) -> None:
    if path.startswith("~."):
        path = f"nonebot_plugin_alconna{path[1:]}"
    elif path.startswith("~"):
        path = f"nonebot_plugin_alconna.{path[1:]}"
    match = pattern.match(path)
    module = imp.import_module(match.group("module"))
    attrs = filter(None, (match.group("attr") or "__extension__").split("."))
    ext = functools.reduce(getattr, attrs, module)
    if isinstance(ext, type) and issubclass(ext, Extension):
        add_global_extension(ext)
    elif isinstance(ext, Extension):
        add_global_extension(ext)
    else:
        raise TypeError(lang.require("nbp-alc", "error.extension_path_load").format(path=path))
