from collections import deque
from typing import Deque, ClassVar, Optional, final

from nonebot import get_driver
from arclet.alconna import Alconna
from nonebot.adapters.telegram import Bot as TelegramBot
from nonebot.adapters.telegram.model import BotCommand, BotCommandScope, BotCommandScopeDefault

from nonebot_plugin_alconna import Extension

commands: "Deque[BotCommand]" = deque(maxlen=100)


@final
class TelegramSlashExtension(Extension):
    """
    用于将 Alconna 的命令自动转换为 Telegram 的 Command。

    Example:
        ```python
        from nonebot_plugin_alconna import on_alconna
        from nonebot.adapters.telegram import BotCommandScopeAllChat
        from nonebot_plugin_alconna.builtins.extensions import TelegramCommandExtension

        TelegramCommandExtension.set_scope(BotCommandScopeAllChat())

        matcher = on_alconna(..., extensions=[TelegramSlashExtension()])
        ```
    """

    SCOPE: ClassVar[BotCommandScope] = BotCommandScopeDefault()
    LANGUAGE_CODE: ClassVar[Optional[str]] = None

    @classmethod
    def set_scope(cls, scope: BotCommandScope) -> None:
        cls.SCOPE = scope

    @classmethod
    def set_language_code(cls, language_code: Optional[str]) -> None:
        cls.LANGUAGE_CODE = language_code

    @property
    def priority(self) -> int:
        return 10

    @property
    def id(self) -> str:
        return "builtins.extensions.telegram:TelegramSlashExtension"

    def __init__(self):
        self.using = False

    def post_init(self, alc: Alconna) -> None:
        if alc.prefixes != ["/"] or (
            not alc.prefixes and isinstance(alc.command, str) and not alc.command.startswith("/")
        ):
            return
        self.using = True
        if alc.prefixes == ["/"]:
            command = alc.command
        else:
            command = alc.command[1:]
        commands.append(BotCommand(command=command, description=alc.meta.description))

    def validate(self, bot, event) -> bool:
        return self.using


driver = get_driver()


@driver.on_bot_connect
async def on_bot_connect(bot: TelegramBot):
    await bot.set_my_commands(
        commands=list(commands),
        scope=TelegramSlashExtension.SCOPE,
        language_code=TelegramSlashExtension.LANGUAGE_CODE,
    )


__extension__ = TelegramSlashExtension
