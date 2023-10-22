import asyncio
from typing import List, Type, Union, Optional, cast

from nonebot import get_driver
from nonebot.typing import T_State
from nonebot.matcher import matchers
from nonebot.params import EventMessage
from nonebot.plugin.on import on_message
from nonebot.internal.rule import Rule as Rule
from nonebot.permission import User, Permission
from nonebot.adapters import Bot, Event, Message
from tarina import lang, init_spec, is_awaitable
from arclet.alconna.exceptions import SpecialOptionTriggered
from arclet.alconna import Alconna, Arparma, CompSession, output_manager, command_manager

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
        "_session",
        "_waiter",
        "_future",
        "_interface",
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
                self.comp_config = cast(CompConfig, {})
            self.use_origin = use_origin or config.alconna_use_origin
        except ValueError:
            self.auto_send = auto_send_output
        self.command = command
        self.skip = skip_for_unmatch
        self.executor = ExtensionExecutor(self, extensions, exclude_ext)
        self.executor.post_init()
        self._session = None
        self._future: asyncio.Future = asyncio.Future()
        self._interface = CompSession(self.command)
        self._waiter = on_message(
            priority=0,
            block=True,
            rule=Rule(lambda: self._session is not None),
        )
        self._waiter.destroy()
        if self.comp_config is not None:
            _tab = self.comp_config.get("tab", ".tab")
            _enter = self.comp_config.get("enter", ".enter")
            _exit = self.comp_config.get("exit", ".exit")

            @self._waiter.handle()
            async def _waiter_handle(_bot: Bot, _event: Event, content: Message = EventMessage()):
                msg = str(content)
                if msg.startswith(_exit):
                    if msg == _exit:
                        self._future.set_result(False)
                        await self._waiter.finish()
                    else:
                        self._future.set_result(None)
                        await self._waiter.pause(
                            lang.require("analyser", "param_unmatched").format(
                                target=msg.replace(_exit, "", 1)
                            )
                        )
                elif msg.startswith(_enter):
                    if msg == _enter:
                        self._future.set_result(True)
                        await self._waiter.finish()
                    else:
                        self._future.set_result(None)
                        await self._waiter.pause(
                            lang.require("analyser", "param_unmatched").format(
                                target=msg.replace(_enter, "", 1)
                            )
                        )
                elif msg.startswith(_tab):
                    offset = msg.replace(_tab, "", 1).lstrip() or 1
                    try:
                        offset = int(offset)
                    except ValueError:
                        self._future.set_result(None)
                        await self._waiter.pause(
                            lang.require("analyser", "param_unmatched").format(target=offset)
                        )
                    else:
                        self._interface.tab(offset)
                        if self.comp_config is not None and self.comp_config.get("lite", False):
                            out = f"* {self._interface.current()}"
                        else:
                            out = "\n".join(self._interface.lines())
                        self._future.set_result(None)
                        await self._waiter.pause(out)
                else:
                    self._future.set_result(content)
                    await self._waiter.finish()

    def __repr__(self) -> str:
        return f"Alconna(command={self.command!r})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, AlconnaRule) and self.command.path == other.command.path

    def __hash__(self) -> int:
        return hash(self.command.__hash__())

    async def handle(self, bot: Bot, event: Event, msg: Message):
        if self.comp_config is None:
            return self.command.parse(msg)
        res = None
        with self._interface:
            res = self.command.parse(msg)
        if res:
            return res
        self._session = event.get_session_id()
        self._waiter.permission = Permission(User.from_event(event))
        matchers[self._waiter.priority].append(self._waiter)
        res = Arparma(
            self.command.path,
            msg,
            False,
            error_info=SpecialOptionTriggered("completion"),
        )

        help_text = (
            f"{lang.require('comp/nonebot', 'tab').format(cmd=self.comp_config.get('tab', '.tab'))}\n"
            f"{lang.require('comp/nonebot', 'enter').format(cmd=self.comp_config.get('enter', '.enter'))}\n"
            f"{lang.require('comp/nonebot', 'exit').format(cmd=self.comp_config.get('exit', '.exit'))}\n"
            f"{lang.require('comp/nonebot', 'other')}\n"
        )

        while self._interface.available:
            await self.send(f"{str(self._interface)}\n\n{help_text}", bot, event, res)
            while True:
                self._future = asyncio.get_running_loop().create_future()
                try:
                    await asyncio.wait_for(self._future, timeout=self.comp_config.get("timeout", 60))
                except asyncio.TimeoutError:
                    await self.send(lang.require("comp/nonebot", "timeout"), bot, event, res)
                    self._interface.exit()
                    self._waiter.destroy()
                    return res
                finally:
                    if not self._future.done():
                        self._future.cancel()
                ans: Union[Message, bool, None] = self._future.result()
                if ans is False:
                    await self.send(lang.require("comp/nonebot", "exited"), bot, event, res)
                    self._interface.exit()
                    self._waiter.destroy()
                    return res
                elif ans is None:
                    continue
                _res = self._interface.enter(None if ans is True else ans)
                if _res.result:
                    res = _res.result
                elif _res.exception and not isinstance(_res.exception, SpecialOptionTriggered):
                    await self.send(str(_res.exception), bot, event, res)
                break
        self._interface.exit()
        self._waiter.destroy()
        return res

    async def __call__(self, event: Event, state: T_State, bot: Bot) -> bool:
        self.executor.select(bot, event)
        if not (msg := await self.executor.message_provider(event, state, bot, self.use_origin)):
            return False
        msg = await self.executor.receive_wrapper(bot, event, msg)
        if isinstance(msg, UniMessage):
            msg = await msg.export(bot, fallback=True)
        Arparma._additional.update(bot=lambda: bot, event=lambda: event, state=lambda: state)
        if self._session and self._session != event.get_session_id():
            return False
        with output_manager.capture(self.command.name) as cap:
            output_manager.set_action(lambda x: x, self.command.name)
            try:
                arp = await self.handle(bot, event, msg)
            except Exception as e:
                arp = Arparma(self.command.path, msg, False, error_info=e)
            may_help_text: Optional[str] = cap.get("output", None)
        self._session = None
        if not arp.matched and not may_help_text and self.skip:
            log("TRACE", lang.require("nbp-alc", "log.parse").format(msg=msg, cmd=self.command.path, arp=arp))
            return False
        if arp.head_matched:
            log("DEBUG", lang.require("nbp-alc", "log.parse").format(msg=msg, cmd=self.command.path, arp=arp))
        if not may_help_text and arp.error_info:
            may_help_text = repr(arp.error_info)
        if self.auto_send and may_help_text:
            await self.send(may_help_text, bot, event, arp)
            return False
        await self.executor.parse_wrapper(bot, state, event, arp)
        state[ALCONNA_RESULT] = CommandResult(self.command, arp, may_help_text)
        exec_result = self.command.exec_result
        for key, value in exec_result.items():
            if is_awaitable(value):
                value = await value
            if isinstance(value, (str, Message)):
                value = await bot.send(event, value)
            exec_result[key] = value
        state[ALCONNA_EXEC_RESULT] = exec_result
        state[ALCONNA_EXTENSION] = self.executor.context
        return True

    async def send(self, text: str, bot: Bot, event: Event, arp: Arparma) -> Message:
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
