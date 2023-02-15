from typing import Callable, Awaitable, ClassVar, cast, Type, Optional, Union
from typing_extensions import get_args
from inspect import signature
from arclet.alconna import Alconna, Arparma, Duplication, output_manager
from nonebot.adapters import Message, Bot, Event
from nonebot.internal.rule import Rule as Rule
from nonebot.typing import T_State
from nonebot.utils import run_sync, is_coroutine_callable

from .consts import ALCONNA_RESULT
from .model import CommandResult


class AlconnaRule:
    """检查消息字符串是否能够通过此 Alconna 命令。

    参数:
        command: Alconna 命令
        checker: 命令解析结果的检查器
        duplication: 可选的自定义 Duplication 类型
        skip_for_unmatch: 是否在命令不匹配时跳过该响应
        auto_send_output: 是否自动发送输出信息并跳过响应
        output_converter: 输出信息字符串转换为 Message 方法
    """

    default_converter: ClassVar[
        Callable[[str],  Union[Message, Awaitable[Message]]]
    ] = lambda x: Message(x)

    __slots__ = ("command", "duplication", "skip", "checkers", "auto_send", "output_converter")

    def __init__(
        self,
        command: Alconna,
        *checker: Callable[[Arparma], bool],
        duplication: Optional[Type[Duplication]] = None,
        skip_for_unmatch: bool = True,
        auto_send_output: bool = False,
        output_converter: Optional[Callable[[str],  Union[Message, Awaitable[Message]]]] = None
    ):
        self.command = command
        self.duplication = duplication
        self.skip = skip_for_unmatch
        self.checkers = checker
        self.auto_send = auto_send_output
        self.output_converter = output_converter or self.__class__.default_converter
        if not is_coroutine_callable(self.output_converter):
            self.output_converter = run_sync(self.output_converter)

    def __repr__(self) -> str:
        return f"Alconna(command={self.command!r}, duplication={self.duplication})"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, AlconnaRule)
            and self.command.path == other.command.path
            and self.duplication == other.duplication
        )

    def __hash__(self) -> int:
        return hash((self.command.__hash__(), self.duplication))

    async def __call__(self, event: Event, state: T_State, bot: Bot) -> bool:
        if event.get_type() != "message":
            return False
        try:
            msg = getattr(event, 'original_message', event.get_message())
        except NotImplementedError:
            return False
        with output_manager.capture(self.command.name) as cap:
            output_manager.set_action(lambda x: x, self.command.name)
            try:
                arp = self.command.parse(msg)
            except Exception as e:
                arp = Arparma(self.command.path, msg, False, error_info=repr(e))
            may_help_text: Optional[str] = cap.get("output", None)
        if (
            not may_help_text
            and not arp.matched
            and ((not arp.head_matched) or self.skip)
        ):
            return False
        if self.auto_send and may_help_text:
            try:
                await bot.send(event, await self.output_converter(may_help_text))
            except NotImplementedError:
                msg_anno = signature(bot.send).parameters['message'].annotation
                msg_type = cast(Type[Message], next(filter(lambda x: x.__name__ == "Message", get_args(msg_anno))))
                await bot.send(event, msg_type(may_help_text))
            return False
        for checker in self.checkers:
            if not checker(arp):
                return False
        state[ALCONNA_RESULT] = CommandResult(
            arp.token, may_help_text, self.duplication
        )
        return True


def alconna(
    command: Alconna,
    *checker: Callable[[Arparma], bool],
    duplication: Optional[Type[Duplication]] = None,
    skip_for_unmatch: bool = True,
    auto_send_output: bool = False,
    output_converter: Optional[Callable[[str], Union[Message, Awaitable[Message]]]] = None
) -> Rule:
    return Rule(
        AlconnaRule(
            command,
            *checker,
            duplication=duplication,
            skip_for_unmatch=skip_for_unmatch,
            auto_send_output=auto_send_output,
            output_converter=output_converter
        )
    )


def set_converter(fn: Callable[[str], Union[Message, Awaitable[Message]]]):
    AlconnaRule.default_converter = fn
