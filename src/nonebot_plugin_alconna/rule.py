import asyncio
from typing import Awaitable, Callable, ClassVar, List, Optional, Type, Union, cast, Dict

from arclet.alconna import (
    Alconna,
    Arparma,
    Args,
    CommandMeta,
    CompSession,
    AllParam,
    command_manager,
    output_manager,
)
import traceback
from arclet.alconna.exceptions import SpecialOptionTriggered
from nonebot import get_driver
from nonebot.adapters import Bot, Event, Message
from nonebot.internal.rule import Rule as Rule
from nonebot.plugin.on import on_message
from nonebot.params import EventMessage
from nonebot.typing import T_State
from nonebot.utils import is_coroutine_callable, run_sync
from tarina import lang
from typing_extensions import get_args, get_type_hints

from .config import Config
from .consts import ALCONNA_RESULT
from .model import CommandResult, CompConfig
from .typings import OutputType


class AlconnaRule:
    """检查消息字符串是否能够通过此 Alconna 命令。

    参数:
        command: Alconna 命令
        checker: 命令解析结果的检查器
        skip_for_unmatch: 是否在命令不匹配时跳过该响应
        auto_send_output: 是否自动发送输出信息并跳过响应
        output_converter: 输出信息字符串转换为 Message 方法
        comp_config: 自动补全配置
    """

    default_converter: ClassVar[
        Callable[[OutputType, str], Union[Message, Awaitable[Message]]]
    ] = lambda _, x: Message(x)

    __slots__ = (
        "command",
        "skip",
        "checkers",
        "auto_send",
        "output_converter",
        "comp_config",
    )

    def __init__(
        self,
        command: Alconna,
        checker: Optional[List[Callable[[Arparma], bool]]] = None,
        skip_for_unmatch: bool = True,
        auto_send_output: bool = False,
        output_converter: Optional[
            Callable[[OutputType, str], Union[Message, Awaitable[Message]]]
        ] = None,
        comp_config: Optional[CompConfig] = None,
    ):
        self.comp_config = comp_config
        try:
            global_config = get_driver().config
            config = Config.parse_obj(global_config)
            self.auto_send = auto_send_output or config.alconna_auto_send_output
            if config.alconna_use_command_start and global_config.command_start:
                command_manager.delete(command)
                command.prefixes = list(global_config.command_start)
                command._hash = command._calc_hash()
                command_manager.register(command)
            if config.alconna_auto_completion and not self.comp_config:
                self.comp_config = {}
        except ValueError:
            self.auto_send = auto_send_output
        self.command = command
        self.skip = skip_for_unmatch
        self.checkers = checker
        self.output_converter = output_converter or self.__class__.default_converter
        if not is_coroutine_callable(self.output_converter):
            self.output_converter = run_sync(self.output_converter)

    def __repr__(self) -> str:
        return f"Alconna(command={self.command!r})"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, AlconnaRule) and self.command.path == other.command.path
        )

    def __hash__(self) -> int:
        return hash(self.command.__hash__())

    async def handle(self, bot: Bot, event: Event, msg: Message):
        interface = CompSession(self.command)
        if self.comp_config is None:
            return self.command.parse(msg)
        _tab = Alconna(
            self.comp_config.get("tab", ".tab"),
            Args["offset", int, 1], meta=CommandMeta(hide=True, compact=True)
        )
        _enter = Alconna(
            self.comp_config.get("enter", ".enter"),
            Args["content", AllParam, []], meta=CommandMeta(hide=True, compact=True)
        )
        _exit = Alconna(
            self.comp_config.get("exit", ".exit"),
            meta=CommandMeta(hide=True, compact=True)
        )
        _waiter = on_message(priority=self.comp_config.get('priority', -100), block=True)
        _futures: Dict[str, asyncio.Future] = {}

        @_waiter.handle()
        async def _waiter_handle(content: Message = EventMessage()):
            if _exit.parse(content).matched:
                _futures["_"].set_result(False)
                await _waiter.finish()
            if (mat := _tab.parse(content)).matched:
                interface.tab(mat.offset)
                await self.send("\n".join(interface.lines()), bot, event, res)
                await _waiter.reject()
            if (mat := _enter.parse(content)).matched:
                _futures["_"].set_result(mat.content)
                await _waiter.finish()
            await self.send(interface.current(), bot, event, res)
            await _waiter.reject()

        def clear():
            interface.clear()
            _waiter.destroy()
            command_manager.delete(_tab)
            command_manager.delete(_enter)
            command_manager.delete(_exit)

        with interface:
            res = self.command.parse(msg)
        while interface.available:
            res = Arparma(self.command.path, msg, False, error_info=SpecialOptionTriggered("completion"))
            await self.send(str(interface), bot, event, res)
            await self.send(
                f"{lang.require('alconna/nonebot', 'tab').format(cmd=_tab.command)}\n"
                f"{lang.require('alconna/nonebot', 'enter').format(cmd=_enter.command)}\n"
                f"{lang.require('alconna/nonebot', 'exit').format(cmd=_exit.command)}",
                bot, event, res
            )
            _future = _futures.setdefault("_", asyncio.get_running_loop().create_future())
            _future.add_done_callback(lambda x: _futures.pop("_"))
            try:
                await asyncio.wait_for(_future, timeout=60)
            except asyncio.TimeoutError:
                clear()
                return res
            content: Union[Message, bool] = _future.result()
            if content is False:
                clear()
                return res
            param = list(content)
            if not param or not param[0]:
                param = None
            try:
                with interface:
                    res = interface.enter(param)
            except Exception as e:
                traceback.print_exc()
                await self.send(str(e), bot, event, res)
        clear()
        return res

    async def __call__(self, event: Event, state: T_State, bot: Bot) -> bool:
        if event.get_type() != "message":
            return False
        try:
            msg = getattr(event, "original_message", event.get_message())
        except (NotImplementedError, ValueError):
            return False
        with output_manager.capture(self.command.name) as cap:
            output_manager.set_action(lambda x: x, self.command.name)
            try:
                arp = await self.handle(bot, event, msg)
            except Exception as e:
                arp = Arparma(self.command.path, msg, False, error_info=repr(e))
            may_help_text: Optional[str] = cap.get("output", None)
        if not may_help_text and not arp.matched and not arp.head_matched and self.skip:
            return False
        if self.auto_send and may_help_text:
            await self.send(may_help_text, bot, event, arp)
            return False
        for checker in self.checkers:
            if not checker(arp):
                return False
        state[ALCONNA_RESULT] = CommandResult(arp, may_help_text)
        return True

    async def send(self, text: str, bot: Bot, event: Event, arp: Arparma):
        try:
            _t = (
                str(arp.error_info)
                if isinstance(arp.error_info, SpecialOptionTriggered)
                else "help"
            )
            await bot.send(event, await self.output_converter(_t, text))  # type: ignore
        except NotImplementedError:
            msg_anno = get_type_hints(bot.send)["message"]
            msg_type = cast(
                Type[Message],
                next(filter(lambda x: x.__name__ == "Message", get_args(msg_anno))),
            )
            await bot.send(event, msg_type(text))


def alconna(
    command: Alconna,
    checker: Optional[List[Callable[[Arparma], bool]]] = None,
    skip_for_unmatch: bool = True,
    auto_send_output: bool = False,
    output_converter: Optional[
        Callable[[OutputType, str], Union[Message, Awaitable[Message]]]
    ] = None,
    comp_config: Optional[CompConfig] = None,
) -> Rule:
    return Rule(
        AlconnaRule(
            command,
            checker,
            skip_for_unmatch,
            auto_send_output,
            output_converter,
            comp_config,
        )
    )


def set_output_converter(fn: Callable[[OutputType, str], Union[Message, Awaitable[Message]]]):
    AlconnaRule.default_converter = fn
