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
    """ButtonInteraction对象，表示一类按钮回调

    Args:
        bot: 当前 Bot
        event: 原始事件
        id: 按钮 id
        data: 按钮回调数据
        user_id: 点击按钮的用户 id
    """

    def __init__(self, bot: Bot, event: Event, id: str | None, data: str | None = None, *, user_id: str):
        self.bot = bot
        self.event = event
        self.id = id
        self.data = data
        self.user_id = user_id


class ButtonInteractionAdapter(ABC):
    """按钮回调适配器。"""

    @abstractmethod
    async def extract_button(self, bot: Bot, event: Event) -> ButtonInteraction | None:
        """应答按钮回调并返回 ButtonInteraction，其他事件返回 None。"""
        raise NotImplementedError


async def get_button_interaction(bot: Bot, event: Event, state: T_State) -> ButtonInteraction | None:
    """获取按钮回调，非按钮事件或不支持的平台返回 None。"""
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
    """匹配指定 id 的按钮回调，不传入 id 时匹配所有按钮。"""
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
    """注册一个按钮事件响应器。

    参数:
        ids: 按钮 id，不传入则响应所有按钮
        rule: 事件响应规则
        permission: 事件响应权限
        handlers: 事件处理函数列表
        temp: 是否为临时事件响应器（仅执行一次）
        expire_time: 事件响应器最终有效时间点，过时即被删除
        priority: 事件响应器优先级
        block: 是否阻止事件向更低优先级传递
        state: 默认 state
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
