from __future__ import annotations

from arclet.alconna import Alconna
from nonebot.internal.adapter import Bot, Event
from nonebot.permission import SuperUser

from nonebot_plugin_alconna import Extension, UniMessage


class SuperUserShortcutExtension(Extension):
    """
    用于设置仅超级用户可使用内置选项 `--shortcut` 的扩展。

    Example:
        >>> from nonebot_plugin_alconna.builtins.extensions.shortcut import SuperUserShortcutExtension
        >>>
        >>> matcher = on_alconna("...", extensions=[SuperUserShortcutExtension()])
    """

    @property
    def priority(self) -> int:
        return 20

    @property
    def id(self) -> str:
        return "builtins.extensions.shortcut:SuperUserShortcutExtension"

    async def receive_wrapper(self, bot: Bot, event: Event, command: Alconna, receive: UniMessage) -> UniMessage:
        su = SuperUser()
        if await su(bot, event):
            command.namespace_config.disable_builtin_options.discard("shortcut")
        else:
            command.namespace_config.disable_builtin_options.add("shortcut")
        return receive


__extension__ = SuperUserShortcutExtension
