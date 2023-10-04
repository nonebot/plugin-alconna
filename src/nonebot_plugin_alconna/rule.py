import asyncio
import traceback
from typing import Dict, List, Type, Union, Literal, Optional

from nonebot import get_driver
from nonebot.typing import T_State
from nonebot.params import EventMessage
from nonebot.plugin.on import on_message
from nonebot.internal.matcher import matchers
from nonebot.internal.rule import Rule as Rule
from nonebot.adapters import Bot, Event, Message
from tarina import lang, init_spec, is_awaitable
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
from .uniseg import UniMessage
from .model import CompConfig, CommandResult
from .extension import Extension, ExtensionExecutor
from .consts import ALCONNA_RESULT, ALCONNA_EXTENSION, ALCONNA_EXEC_RESULT, log


class AlconnaRule:
    """检查消息字符串是否能够通过此 Alconna 命令。

    参数:
        command: Alconna 命令
        skip_for_unmatch: 是否在命令不匹配时跳过该响应
        auto_send_output: 是否自动发送输出信息并跳过响应
        comp_config: 自动补全配置
        extensions: 需要加载的匹配扩展
        exclude_ext: 需要排除的匹配扩展
        use_origin: 是否使用未经 to_me 等处理过的消息
        use_cmd_start: 是否使用 nb 全局配置里的命令前缀
    """

    __slots__ = (
        "command",
        "skip",
        "auto_send",
        "comp_config",
        "use_origin",
        "executor",
    )

    def __init__(
        self,
        command: Alconna,
        skip_for_unmatch: bool = True,
        auto_send_output: bool = False,
        comp_config: Optional[CompConfig] = None,
        extensions: Optional[List[Union[Type[Extension], Extension]]] = None,
        exclude_ext: Optional[List[Union[Type[Extension], str]]] = None,
        use_origin: bool = False,
        use_cmd_start: bool = False,
        use_cmd_sep: bool = False,
    ):
        self.comp_config = comp_config
        self.use_origin = use_origin
        try:
            global_config = get_driver().config
            config = Config.parse_obj(global_config)
            self.auto_send = auto_send_output or config.alconna_auto_send_output
            if (
                not command.prefixes
                and (use_cmd_start or config.alconna_use_command_start)
                and global_config.command_start
            ):
                command_manager.delete(command)
                command.prefixes = list(global_config.command_start)
                command._hash = command._calc_hash()
                command_manager.register(command)
            if (use_cmd_sep or config.alconna_use_command_sep) and global_config.command_sep:
                command.separators = tuple(global_config.command_sep)
                command_manager.resolve(command).separators = tuple(global_config.command_sep)
            if config.alconna_auto_completion and not self.comp_config:
                self.comp_config = {}
            self.use_origin = use_origin or config.alconna_use_origin
        except ValueError:
            self.auto_send = auto_send_output
        self.command = command
        self.skip = skip_for_unmatch
        self.executor = ExtensionExecutor(extensions, exclude_ext)
        self.executor.post_init(self.command)

    def __repr__(self) -> str:
        return f"Alconna(command={self.command!r})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, AlconnaRule) and self.command.path == other.command.path

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
        _tab = Alconna(self.comp_config.get("tab", ".tab"), Args["offset", int, 1], [], meta=meta)
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
        async def _waiter_handle(_bot: Bot, _event: Event, content: Message = EventMessage()):
            if _exit.parse(content).matched:
                _futures["_"].set_result(False)
                await _waiter.finish()
            if (mat := _tab.parse(content)).matched:
                interface.tab(mat.query[int]("offset", 1))
                if self.comp_config.get("lite", False):  # type: ignore
                    out = interface.current()
                else:
                    out = "\n".join(interface.lines())
                await self._send(out, _bot, _event, res)  # type: ignore
                _waiter.skip()
            if (mat := _enter.parse(content)).matched:
                _futures["_"].set_result(mat.content)
                await _waiter.finish()
            await self._send(interface.current(), _bot, _event, res)  # type: ignore
            _waiter.skip()

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
            await self._send(str(interface), bot, event, res)
            await self._send(help_text, bot, event, res)
            _future = _futures.setdefault("_", asyncio.get_running_loop().create_future())
            _future.add_done_callback(lambda x: _futures.pop("_"))
            try:
                await asyncio.wait_for(_future, timeout=self.comp_config.get("timeout", 60))
            except asyncio.TimeoutError:
                await self._send(lang.require("comp/nonebot", "timeout"), bot, event, res)
                clear()
                return res
            ans: Union[Message, Literal[False]] = _future.result()
            if ans is False:
                await self._send(lang.require("comp/nonebot", "exited"), bot, event, res)
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
                await self._send(str(e), bot, event, res)
        clear()
        return res

    async def __call__(self, event: Event, state: T_State, bot: Bot) -> bool:
        self.executor.select(bot, event)
        if not (msg := await self.executor.message_provider(event, state, bot, self.use_origin)):
            return False
        elif isinstance(msg, UniMessage):
            msg = await msg.export(bot, fallback=True)
        Arparma._additional.update(bot=lambda: bot, event=lambda: event, state=lambda: state)
        with output_manager.capture(self.command.name) as cap:
            output_manager.set_action(lambda x: x, self.command.name)
            try:
                arp = await self.handle(bot, event, msg)
            except Exception as e:
                arp = Arparma(self.command.path, msg, False, error_info=e)
            may_help_text: Optional[str] = cap.get("output", None)
        if not arp.matched and not may_help_text and self.skip:
            return False
        if arp.head_matched:
            log("DEBUG", f'Parse result of "{msg}" by {self.command.path} is ({arp})')
        if not may_help_text and arp.error_info:
            may_help_text = repr(arp.error_info)
        if self.auto_send and may_help_text:
            await self._send(may_help_text, bot, event, arp)
            return False
        state[ALCONNA_RESULT] = CommandResult(self.command, arp, may_help_text)
        exec_result = self.command.exec_result
        for key, value in exec_result.items():
            if is_awaitable(value):
                exec_result[key] = await value
            elif isinstance(value, (str, Message)):
                exec_result[key] = await bot.send(event, value)
        state[ALCONNA_EXEC_RESULT] = exec_result
        state[ALCONNA_EXTENSION] = self.executor.context
        return True

    async def _send(self, text: str, bot: Bot, event: Event, arp: Arparma) -> Message:
        _t = str(arp.error_info) if isinstance(arp.error_info, SpecialOptionTriggered) else "help"
        try:
            msg = await self.executor.output_converter(_t, text)  # type: ignore
            if isinstance(msg, UniMessage):
                msg = await msg.export(bot, fallback=True)
            return await bot.send(event, msg)  # type: ignore
        except NotImplementedError:
            return await bot.send(event, event.get_message().__class__(text))


@init_spec(AlconnaRule)
def alconna(rule: AlconnaRule) -> Rule:
    return Rule(rule)
