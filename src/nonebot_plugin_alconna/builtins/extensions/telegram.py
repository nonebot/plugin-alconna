from collections import deque
from typing import ClassVar, Optional, final

from nonebot import get_driver
from arclet.alconna import Alconna
from nonebot.adapters.telegram import Bot as TelegramBot
from nonebot.adapters.telegram.model import BotCommand, BotCommandScope, BotCommandScopeDefault

from nonebot_plugin_alconna import Extension

commands: "deque[BotCommand]" = deque(maxlen=100)


@final
class TelegramSlashExtension(Extension):
    """
    用于将 Alconna 的命令自动转换为 Telegram 的 Command。

    Example:
        ```python
        from nonebot_plugin_alconna import on_alconna
        from nonebot.adapters.telegram.model import BotCommandScopeChat
        from nonebot_plugin_alconna.builtins.extensions.telegram import TelegramCommandExtension

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
        return 12

    @property
    def id(self) -> str:
        return "builtins.extensions.telegram:TelegramSlashExtension"

    def __init__(self):
        self.using = False

    def post_init(self, alc: Alconna) -> None:
        if "/" not in alc.prefixes or (
            not alc.prefixes and isinstance(alc.command, str) and not alc.command.startswith("/")
        ):
            return
        self.using = True
        if alc.command.startswith("/"):
            command = alc.command[1:]
        else:
            command = alc.command
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
