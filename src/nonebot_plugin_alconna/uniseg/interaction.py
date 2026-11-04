from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any

from nonebot.adapters import Bot, Event
from nonebot.dependencies import Dependent
from nonebot.exception import SkippedException
from nonebot.matcher import Matcher
from nonebot.message import event_preprocessor
from nonebot.params import Depends
from nonebot.permission import Permission
from nonebot.plugin.on import get_matcher_source, store_matcher
from nonebot.rule import Rule
from nonebot.typing import T_Handler, T_PermissionChecker, T_RuleChecker, T_State

from .constraint import UNISEG_BUTTON_INTERACTION


class ButtonInteraction:
    """已完成必要平台回执的按钮事件。

    ``id`` 对应发送时的 ``Button.id``；平台未提供时为 ``None``。
    ``data`` 保留平台提供的回调文本，不从按钮标题或 ID 推测额外数据。
    """

    def __init__(self, bot: Bot, event: Event, id: str | None, data: str | None = None):
        self.bot = bot
        self.event = event
        self.id = id
        self.data = data


class ButtonInteractionAdapter(ABC):
    """平台按钮回调适配：完成平台回执后返回统一事件。"""

    @abstractmethod
    async def extract_button(self, bot: Bot, event: Event) -> ButtonInteraction | None:
        """完成必要 ACK 并返回按钮上下文；其他事件返回 None。"""
        raise NotImplementedError


async def get_button_interaction(bot: Bot, event: Event, state: T_State) -> ButtonInteraction | None:
    """取得本次事件分发的按钮上下文，不支持的平台或非按钮事件返回 None。

    上下文保存在事件 state，普通 matcher 与嵌套 Waiter 共享同一次解析和 ACK。
    """
    if UNISEG_BUTTON_INTERACTION in state:
        return state[UNISEG_BUTTON_INTERACTION]
    from .adapters import alter_get_interaction

    adapter = alter_get_interaction(bot.adapter.get_name())
    interaction = await adapter.extract_button(bot, event) if adapter is not None else None
    state[UNISEG_BUTTON_INTERACTION] = interaction
    return interaction


@event_preprocessor
async def _require_button_interaction(
    interaction: ButtonInteraction | None = Depends(get_button_interaction),
) -> ButtonInteraction:
    """预处理与业务注入共用依赖缓存，避免并发重复 ACK。"""
    if interaction is None:
        raise SkippedException
    return interaction


class _ButtonRule:
    def __init__(self, ids: tuple[str, ...]):
        self.ids = frozenset(ids)

    async def __call__(
        self,
        interaction: ButtonInteraction | None = Depends(get_button_interaction),
    ) -> bool:
        return interaction is not None and (not self.ids or interaction.id in self.ids)


def button_rule(*ids: str) -> Rule:
    """匹配原生按钮回调，不提供 ID 时匹配所有已支持的按钮事件。

    规则只做匹配，不 ACK；可以组合其他 NoneBot 规则以及 Waiter。
    """
    return Rule(_ButtonRule(ids))


def on_button(
    *ids: str,
    rule: Rule | T_RuleChecker | None = None,
    permission: Permission | T_PermissionChecker | None = None,
    handlers: list[T_Handler | Dependent[Any]] | None = None,
    temp: bool = False,
    expire_time: datetime | timedelta | None = None,
    priority: int = 1,
    block: bool = True,
    state: T_State | None = None,
    _depth: int = 0,
) -> type[Matcher]:
    """监听原生按钮点击，不经过命令解析，也不创建伪造消息事件。

    handler、规则和 Waiter 统一通过 ``ButtonCallback`` 或
    ``UniversalButtonInteraction()`` 注入按钮上下文。

    平台 ACK 已在事件预处理中完成，不受 ID、权限和业务规则匹配结果影响。
    业务只判断是否执行操作，不管理平台回执。
    其余参数与 NoneBot ``on()`` 相同；默认阻止继续传播。
    """
    matcher = Matcher.new(
        type_="",
        rule=button_rule(*ids) & rule,
        permission=Permission() | permission,
        handlers=handlers,
        temp=temp,
        expire_time=expire_time,
        priority=priority,
        block=block,
        default_state=state,
        source=get_matcher_source(_depth + 1),
    )
    store_matcher(matcher)
    return matcher
