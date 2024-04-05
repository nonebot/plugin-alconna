from functools import partial
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Set, Dict, Type, Union, Callable

from nonebot.adapters import Bot, Adapter, Message

from .segment import Reply
from .tools import get_bot
from .constraint import SupportScope, SupportAdapter, SerializeFailed, lang

if TYPE_CHECKING:
    from .message import UniMessage


SCOPES: Dict[str, Callable[["Target", Bot], bool]] = {}


@dataclass(init=False)
class Target:
    id: str
    """目标id；若为群聊则为group_id或者channel_id，若为私聊则为user_id"""
    parent_id: str = ""
    """父级id；若为频道则为guild_id，其他情况为空字符串"""
    channel: bool = False
    """是否为频道，仅当目标平台符合频道概念时"""
    private: bool = False
    """是否为私聊"""
    source: str = ""
    """可能的事件id"""
    self_id: Union[str, None]
    """机器人id，若为 None 则 Bot 对象会随机选择"""
    selector: Union[Callable[[Bot], bool], None]
    """选择器，用于在多个 Bot 对象中选择特定 Bot"""
    extra: Dict[str, Any]
    """额外信息，用于适配器扩展"""

    def __init__(
        self,
        id: str,
        parent_id: str = "",
        channel: bool = False,
        private: bool = False,
        source: str = "",
        self_id: Union[str, None] = None,
        selector: Union[Callable[["Target", Bot], bool], None] = None,
        scope: Union[str, None] = None,
        adapter: Union[str, Type[Adapter], SupportAdapter, None] = None,
        platform: Union[str, Set[str], None] = None,
        extra: Union[Dict[str, Any], None] = None,
    ):
        """初始化 Target 对象

        Args:
            id: 目标id；若为群聊则为 group_id 或者 channel_id，若为私聊则为user_id
            parent_id: 父级id；若为频道则为guild_id，其他情况为空字符串
            channel: 是否为频道，仅当目标平台符合频道概念时
            private: 是否为私聊
            source: 可能的事件id
            self_id: 机器人id，若为 None 则 Bot 对象会随机选择
            selector: 选择器，用于在多个 Bot 对象中选择特定 Bot
            scope: 适配器范围，用于传入内置的特定选择器
            adapter: 适配器名称，若为 None 则需要明确指定 Bot 对象
            platform: 平台名称，仅当目标适配器存在多个平台时使用
            extra: 额外信息，用于适配器扩展
        """
        self.id = id
        self.parent_id = parent_id
        self.channel = channel
        self.private = private
        self.source = source
        self.self_id = self_id
        self.extra = extra if extra else {}
        if selector:
            self.selector = partial(selector, self)
        elif scope:
            self.selector = partial(SCOPES[scope], self)
        else:
            self.selector = None
        if adapter or platform:
            platforms = platform if isinstance(platform, set) else {platform} if platform else set()

            def _predicate(bot: Bot):
                _adapter = bot.adapter
                if not adapter:
                    if not hasattr(bot, "platform") or not platforms:
                        return True
                    return bot.platform in platforms
                if isinstance(adapter, str):
                    if _adapter.get_name() == adapter:
                        if not hasattr(bot, "platform") or not platforms:
                            return True
                        return bot.platform in platforms
                    return False
                if isinstance(_adapter, adapter):
                    if not hasattr(bot, "platform") or not platforms:
                        return True
                    return bot.platform in platforms
                return False

            _selector = self.selector
            self.selector = _predicate if not _selector else lambda bot: _predicate(bot) and _selector(bot)

    @classmethod
    def group(
        cls,
        group_id: str,
        scope: Union[str, None] = None,
        adapter: Union[str, Type[Adapter], SupportAdapter, None] = None,
        platform: Union[str, Set[str], None] = None,
    ):
        return cls(group_id, scope=scope, adapter=adapter, platform=platform)

    @classmethod
    def channel_(
        cls,
        channel_id: str,
        guild_id: str = "",
        scope: Union[str, None] = None,
        adapter: Union[str, Type[Adapter], SupportAdapter, None] = None,
        platform: Union[str, Set[str], None] = None,
    ):
        return cls(channel_id, guild_id, channel=True, scope=scope, adapter=adapter, platform=platform)

    @classmethod
    def user(
        cls,
        user_id: str,
        scope: Union[str, None] = None,
        adapter: Union[str, Type[Adapter], SupportAdapter, None] = None,
        platform: Union[str, Set[str], None] = None,
    ):
        return cls(user_id, private=True, scope=scope, adapter=adapter, platform=platform)

    def select(self):
        if self.self_id:
            return get_bot(bot_id=self.self_id)
        if self.selector:
            return get_bot(predicate=self.selector, rand=True)
        raise SerializeFailed(lang.require("nbp-uniseg", "bot_missing"))

    async def send(
        self,
        message: Union[str, Message, "UniMessage"],
        bot: Union[Bot, None] = None,
        fallback: bool = True,
        at_sender: Union[str, bool] = False,
        reply_to: Union[str, bool, Reply, None] = False,
    ):
        """发送消息"""
        if isinstance(message, str):
            from .message import UniMessage

            message = UniMessage(message)
        if isinstance(message, Message):
            from .message import UniMessage

            message = await UniMessage.generate(message=message, bot=bot)
        return await message.send(self, bot, fallback, at_sender, reply_to)


def _register(scope: SupportScope):
    def decorator(func: Callable[["Target", Bot], bool]):
        SCOPES[scope] = func
        return func

    return decorator


@_register(SupportScope.qq_client)
def select_qq_client(target: "Target", bot: Bot):
    adapter_name = bot.adapter.get_name()
    if target.channel:
        return False
    if adapter_name not in {
        SupportAdapter.mirai,
        SupportAdapter.onebot12,
        SupportAdapter.onebot11,
        SupportAdapter.satori,
    }:
        return False
    if hasattr(bot, "platform"):
        if adapter_name == SupportAdapter.satori and bot.platform not in {"chronocat", "onebot"}:
            return False
        if adapter_name == SupportAdapter.onebot12 and bot.platform != "qq":
            return False
    return True


@_register(SupportScope.qq_api)
def select_qq_api(target: "Target", bot: Bot):
    if bot.adapter.get_name() not in {SupportAdapter.qq, SupportAdapter.satori}:
        return False
    if hasattr(bot, "platform") and bot.platform != "qq":
        return False
    return True


@_register(SupportScope.telegram)
def select_telegram(target: "Target", bot: Bot):
    if bot.adapter.get_name() not in {SupportAdapter.telegram, SupportAdapter.satori}:
        return False
    if hasattr(bot, "platform") and bot.platform != "telegram":
        return False
    return True


@_register(SupportScope.discord)
def select_discord(target: "Target", bot: Bot):
    if not target.channel:
        return False
    if bot.adapter.get_name() not in {SupportAdapter.discord, SupportAdapter.satori, SupportAdapter.onebot12}:
        return False
    if hasattr(bot, "platform") and bot.platform != "discord":
        return False
    return True


@_register(SupportScope.feishu)
def select_feishu(target: "Target", bot: Bot):
    if bot.adapter.get_name() not in {SupportAdapter.feishu, SupportAdapter.satori}:
        return False
    if hasattr(bot, "platform") and bot.platform != "feishu":
        return False
    return True


@_register(SupportScope.dodo)
def select_dodo(target: "Target", bot: Bot):
    if not target.channel:
        return False
    return bot.adapter.get_name() == SupportAdapter.dodo


@_register(SupportScope.kook)
def select_kook(target: "Target", bot: Bot):
    if not target.channel:
        return False
    if bot.adapter.get_name() not in {SupportAdapter.kook, SupportAdapter.satori, SupportAdapter.onebot12}:
        return False
    if hasattr(bot, "platform") and bot.platform not in ("kook", "kaiheila"):
        return False
    return True


@_register(SupportScope.minecraft)
def select_minecraft(target: "Target", bot: Bot):
    if target.channel or target.private:
        return False
    return bot.adapter.get_name() == SupportAdapter.minecraft


@_register(SupportScope.github)
def select_github(target: "Target", bot: Bot):
    if target.channel or target.private:
        return False
    return bot.adapter.get_name() == SupportAdapter.github


@_register(SupportScope.bilibili)
def select_bilibili(target: "Target", bot: Bot):
    if target.channel or target.private:
        return False
    return bot.adapter.get_name() == SupportAdapter.bilibili


@_register(SupportScope.console)
def select_console(target: "Target", bot: Bot):
    if target.channel:
        return False
    return bot.adapter.get_name() == SupportAdapter.console


@_register(SupportScope.ding)
def select_ding(target: "Target", bot: Bot):
    if target.channel:
        return False
    if bot.adapter.get_name() not in {SupportAdapter.ding, SupportAdapter.satori}:
        return False
    if hasattr(bot, "platform") and bot.platform != "dingtalk":
        return False
    return True


@_register(SupportScope.wechat)
def select_wechat(target: "Target", bot: Bot):
    if target.channel:
        return False
    if bot.adapter.get_name() != SupportAdapter.onebot12:
        return False
    if hasattr(bot, "platform") and bot.platform != "wechat":
        return False
    return True


@_register(SupportScope.wechat_oap)
def select_wechat_oap(target: "Target", bot: Bot):
    if target.channel:
        return False
    if bot.adapter.get_name() != SupportAdapter.satori:
        return False
    if hasattr(bot, "platform") and bot.platform != "wechat-official":
        return False
    return True


@_register(SupportScope.wecom)
def select_wecom(target: "Target", bot: Bot):
    if target.channel:
        return False
    if bot.adapter.get_name() != SupportAdapter.satori:
        return False
    if hasattr(bot, "platform") and bot.platform != "wecom":
        return False
    return True
