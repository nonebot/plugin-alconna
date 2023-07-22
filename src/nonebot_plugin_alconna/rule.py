import asyncio
import traceback
from typing import Dict, Union, ClassVar, Optional

from tarina import lang
from nonebot import get_driver
from nonebot.typing import T_State
from nonebot.params import EventMessage
from nonebot.plugin.on import on_message
from nonebot.internal.matcher import matchers
from nonebot.internal.rule import Rule as Rule
from nonebot.adapters import Bot, Event, Message
from nonebot.utils import run_sync, is_coroutine_callable
from arclet.alconna.exceptions import SpecialOptionTriggered
from arclet.alconna import (
    Args,
    Alconna,
    Arparma,
    AllParam,
    CommandMeta,
    CompSession,
    output_manager,
    command_manager,
)

from .config import Config
from .typings import TConvert
from .model import CompConfig, CommandResult
from .consts import ALCONNA_RESULT, ALCONNA_EXEC_RESULT


class AlconnaRule:
    """检查消息字符串是否能够通过此 Alconna 命令。

    参数:
        command: Alconna 命令
        skip_for_unmatch: 是否在命令不匹配时跳过该响应
        auto_send_output: 是否自动发送输出信息并跳过响应
        output_converter: 输出信息字符串转换为 Message 方法
        comp_config: 自动补全配置
    """

    default_converter: ClassVar[TConvert] = lambda _, x: Message(x)

    __slots__ = (
        "command",
        "skip",
        "auto_send",
        "output_converter",
        "comp_config",
    )

    def __init__(
        self,
        command: Alconna,
        skip_for_unmatch: bool = True,
        auto_send_output: bool = False,
        output_converter: Optional[TConvert] = None,
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
        res = None
        with interface:
            res = self.command.parse(msg)
        if res:
            return res
        meta = CommandMeta(compact=True, hide=True)
        _tab = Alconna(
            self.comp_config.get("tab", ".tab"), Args["offset", int, 1], [], meta=meta
        )
        _enter = Alconna(
            self.comp_config.get("enter", ".enter"),
            Args["content", AllParam, []],
            [],
            meta=meta,
        )
        _exit = Alconna(self.comp_config.get("exit", ".exit"), [], meta=meta)

        _waiter = on_message(priority=self.comp_config.get("priority", -1), block=True)
        _futures: Dict[str, asyncio.Future] = {}
        res = Arparma(
            self.command.path,
            msg,
            False,
            error_info=SpecialOptionTriggered("completion"),
        )

        @_waiter.handle()
        async def _waiter_handle(_event: Event, content: Message = EventMessage()):
            if _exit.parse(content).matched:
                _futures["_"].set_result(False)
                await _waiter.finish()
            if (mat := _tab.parse(content)).matched:
                interface.tab(mat.offset)
                await _waiter.send(
                    await self._convert("\n".join(interface.lines()), _event, res)
                )
                await _waiter.skip()
            if (mat := _enter.parse(content)).matched:
                _futures["_"].set_result(mat.content)
                await _waiter.finish()
            await _waiter.send(await self._convert(interface.current(), _event, res))
            await _waiter.skip()

        def clear():
            interface.clear()
            _waiter.destroy()
            _waiter.handlers.clear()
            matchers.pop(-1)
            command_manager.delete(_tab)
            command_manager.delete(_enter)
            command_manager.delete(_exit)

        help_text = (
            f"{lang.require('comp/nonebot', 'tab').format(cmd=_tab.command)}\n"
            f"{lang.require('comp/nonebot', 'enter').format(cmd=_enter.command)}\n"
            f"{lang.require('comp/nonebot', 'exit').format(cmd=_exit.command)}"
        )

        while interface.available:
            await bot.send(event, await self._convert(str(interface), event, res))
            await bot.send(event, await self._convert(help_text, event, res))
            _future = _futures.setdefault(
                "_", asyncio.get_running_loop().create_future()
            )
            _future.add_done_callback(lambda x: _futures.pop("_"))
            try:
                await asyncio.wait_for(
                    _future, timeout=self.comp_config.get("timeout", 60)
                )
            except asyncio.TimeoutError:
                await bot.send(
                    event,
                    await self._convert(
                        lang.require("comp/nonebot", "timeout"), event, res
                    ),
                )
                clear()
                return res
            ans: Union[Message, bool] = _future.result()
            if ans is False:
                await bot.send(
                    event,
                    await self._convert(
                        lang.require("comp/nonebot", "exited"), event, res
                    ),
                )
                clear()
                return res
            param = list(ans)
            if not param or not param[0]:
                param = None
            try:
                with interface:
                    res = interface.enter(param)
            except Exception as e:
                traceback.print_exc()
                await bot.send(event, await self._convert(str(e), event, res))
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
                arp = Arparma(self.command.path, msg, False, error_info=e)
            may_help_text: Optional[str] = cap.get("output", None)
        if not arp.matched and not may_help_text and self.skip:
            return False
        if not may_help_text and arp.error_info:
            may_help_text = repr(arp.error_info)
        if self.auto_send and may_help_text:
            await bot.send(event, await self._convert(may_help_text, event, arp))
            return False
        state[ALCONNA_RESULT] = CommandResult(self.command, arp, may_help_text)
        state[ALCONNA_EXEC_RESULT] = self.command.exec_result
        return True

    async def _convert(self, text: str, event: Event, arp: Arparma) -> Message:
        _t = (
            str(arp.error_info)
            if isinstance(arp.error_info, SpecialOptionTriggered)
            else "help"
        )
        try:
            return await self.output_converter(_t, text)  # type: ignore
        except NotImplementedError:
            return event.get_message().__class__(text)


def alconna(
    command: Alconna,
    skip_for_unmatch: bool = True,
    auto_send_output: bool = False,
    output_converter: Optional[TConvert] = None,
    comp_config: Optional[CompConfig] = None,
) -> Rule:
    return Rule(
        AlconnaRule(
            command,
            skip_for_unmatch,
            auto_send_output,
            output_converter,
            comp_config,
        )
    )


def set_output_converter(fn: TConvert):
    AlconnaRule.default_converter = fn
