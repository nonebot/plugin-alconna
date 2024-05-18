from datetime import datetime
from functools import partial
from abc import ABCMeta, abstractmethod
from collections.abc import Awaitable, AsyncIterator
from typing import TYPE_CHECKING, Any, Union, Callable

from nonebot.adapters import Bot, Adapter, Message

from .segment import Reply
from .tools import get_bot
from .constraint import SupportScope, SupportAdapter, SerializeFailed, lang

if TYPE_CHECKING:
    from .message import UniMessage


SCOPES: dict[str, Callable[["Target", Bot], Awaitable[bool]]] = {}
TARGET_RECORD: dict[str, Callable[["Target"], Awaitable[bool]]] = {}


async def _cache_selector(target: "Target", bot: Bot):
    if bot.self_id in TARGET_RECORD:
        return await TARGET_RECORD[bot.self_id](target)
    return True


class Target:
    id: str
    """目标id；若为群聊则为group_id或者channel_id，若为私聊则为user_id"""
    parent_id: str
    """父级id；若为频道则为guild_id，其他情况下可能为空字符串（例如 Feishu 下可作为部门 id）"""
    channel: bool
    """是否为频道，仅当目标平台符合频道概念时"""
    private: bool
    """是否为私聊"""
    source: str
    """可能的事件id"""
    self_id: Union[str, None]
    """机器人id，若为 None 则 Bot 对象会随机选择"""
    selector: Union[Callable[[Bot], Awaitable[bool]], None]
    """选择器，用于在多个 Bot 对象中选择特定 Bot"""
    extra: dict[str, Any]
    """额外信息，用于适配器扩展"""

    def __init__(
        self,
        id: str,
        parent_id: str = "",
        channel: bool = False,
        private: bool = False,
        source: str = "",
        self_id: Union[str, None] = None,
        selector: Union[Callable[["Target", Bot], Awaitable[bool]], None] = _cache_selector,
        scope: Union[str, None] = None,
        adapter: Union[str, type[Adapter], SupportAdapter, None] = None,
        platform: Union[str, set[str], None] = None,
        extra: Union[dict[str, Any], None] = None,
    ):
        """初始化 Target 对象

        Args:
            id: 目标id；若为群聊则为 group_id 或者 channel_id，若为私聊则为user_id
            parent_id: 若为频道则为guild_id，其他情况下可能为空字符串（例如 Feishu 下可作为部门 id）
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
        self.selector = None
        if scope:
            self.selector = partial(SCOPES[scope], self)
            self.extra["scope"] = scope
        if selector:
            if self.selector:
                _scope_selector = self.selector

                async def _(bot: Bot):
                    return await _scope_selector(bot) and await selector(self, bot)

                self.selector = _
            else:
                self.selector = partial(selector, self)
        if adapter or platform:
            platforms = platform if isinstance(platform, set) else {platform} if platform else set()
            if platforms:
                self.extra["platforms"] = list(platforms)
            if isinstance(adapter, str):
                self.extra["adapter"] = adapter
            elif adapter:
                self.extra["adapter"] = adapter.get_name()

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

            async def _(bot: Bot):
                if not _predicate(bot):
                    return False
                if not _selector:
                    return True
                return await _selector(bot)

            self.selector = _

    def __hash__(self):
        args = (self.id, self.channel, self.private, self.self_id)
        if self.extra.get("scope"):
            args += (self.extra["scope"],)
        if self.extra.get("adapter"):
            args += (str(self.extra["adapter"]),)
        return hash(args)

    def verify(self, other: "Target"):
        if other.id != self.id or other.channel != self.channel or other.private != self.private:
            return False
        if self.parent_id and other.parent_id and self.parent_id != other.parent_id:
            return False
        if self.self_id and other.self_id and self.self_id != other.self_id:
            return False
        if self.extra.get("adapter") and other.extra.get("adapter") and self.extra["adapter"] != other.extra["adapter"]:
            return False
        return True

    def __eq__(self, other):
        return isinstance(other, Target) and self.verify(other)

    @property
    def scope(self) -> Union[str, None]:
        return self.extra.get("scope")

    @property
    def adapter(self) -> Union[str, None]:
        return self.extra.get("adapter")

    @property
    def platform(self) -> Union[list[str], None]:
        return self.extra.get("platforms")

    @classmethod
    def group(
        cls,
        group_id: str,
        scope: Union[str, None] = None,
        adapter: Union[str, type[Adapter], SupportAdapter, None] = None,
        platform: Union[str, set[str], None] = None,
    ):
        return cls(group_id, scope=scope, adapter=adapter, platform=platform)

    @classmethod
    def channel_(
        cls,
        channel_id: str,
        guild_id: str = "",
        scope: Union[str, None] = None,
        adapter: Union[str, type[Adapter], SupportAdapter, None] = None,
        platform: Union[str, set[str], None] = None,
    ):
        return cls(channel_id, guild_id, channel=True, scope=scope, adapter=adapter, platform=platform)

    @classmethod
    def user(
        cls,
        user_id: str,
        scope: Union[str, None] = None,
        adapter: Union[str, type[Adapter], SupportAdapter, None] = None,
        platform: Union[str, set[str], None] = None,
    ):
        return cls(user_id, private=True, scope=scope, adapter=adapter, platform=platform)

    async def select(self):
        if self.self_id:
            try:
                return await get_bot(bot_id=self.self_id)
            except KeyError:
                self.self_id = None
        if self.selector:
            return await get_bot(predicate=self.selector, rand=True)
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

    def dump(self, only_scope: bool = False, save_self_id: bool = True):
        extra = self.extra.copy()
        scope = extra.pop("scope", None)
        adapter = extra.pop("adapter", None)
        platforms = extra.pop("platforms", None)
        data = {
            "id": self.id,
            "parent_id": self.parent_id,
            "channel": self.channel,
            "private": self.private,
            "self_id": self.self_id,
            "extra": extra,
            "scope": scope,
        }
        if not save_self_id:
            data.pop("self_id")
        if not only_scope:
            data["adapter"] = adapter
            data["platforms"] = platforms
        return data

    @classmethod
    def load(cls, data: dict[str, Any]):
        scope = data.pop("scope", None)
        adapter = data.pop("adapter", None)
        platform = data.pop("platforms", None)
        if platform:
            platform = set(platform)  # type: ignore
        return cls(scope=scope, adapter=adapter, platform=platform, **data)

    def __repr__(self):
        return f"Target({self.dump()})"


class TargetFetcher(metaclass=ABCMeta):
    def __init__(self) -> None:
        self.cache: dict[str, set[Target]] = {}
        self.last_refresh: dict[str, datetime] = {}

    @classmethod
    @abstractmethod
    def get_adapter(cls) -> SupportAdapter: ...

    @abstractmethod
    def fetch(self, bot: Bot, target: Union[Target, None] = None) -> AsyncIterator[Target]: ...

    async def refresh(self, bot: Bot, target: Union[Target, None] = None):
        if bot.self_id in self.cache:
            del self.cache[bot.self_id]
        self.last_refresh[bot.self_id] = datetime.now()
        _cache = self.cache.setdefault(bot.self_id, set())
        async for tg in self.fetch(bot, target):
            _cache.add(tg)

    def get_selector(self, bot: Bot):
        async def _check(target: Target):
            if bot.self_id in self.cache:
                targets = self.cache[bot.self_id]
                if target in targets:
                    return True
                target.self_id = bot.self_id
                target.extra["adapter"] = self.get_adapter()
                if target in targets:
                    return True
                for tg in targets:
                    if target.verify(tg):
                        return True
            now = datetime.now()
            if bot.self_id in self.last_refresh and (now - self.last_refresh[bot.self_id]).seconds < 600:
                return False
            self.cache.pop(bot.self_id, None)
            _cache = self.cache.setdefault(bot.self_id, set())
            self.last_refresh[bot.self_id] = now
            count = 0
            async for tg in self.fetch(bot, target):
                _cache.add(tg)
                if target.verify(tg):
                    count += 1
            return count > 0

        return _check


def _register(scope: SupportScope):
    def decorator(func: Callable[["Target", Bot], Awaitable[bool]]):
        SCOPES[scope] = func
        return func

    return decorator


@_register(SupportScope.qq_client)
async def select_qq_client(target: "Target", bot: Bot):
    adapter_name = bot.adapter.get_name()
    if target.channel:
        return False
    if adapter_name not in {
        SupportAdapter.mirai_official,
        SupportAdapter.mirai_community,
        SupportAdapter.onebot12,
        SupportAdapter.onebot11,
        SupportAdapter.satori,
        SupportAdapter.red,
        SupportAdapter.kritor,
    }:
        return False
    if hasattr(bot, "platform"):
        if adapter_name == SupportAdapter.satori and bot.platform not in {"chronocat", "onebot"}:
            return False
        if adapter_name == SupportAdapter.onebot12 and bot.platform != "qq":
            return False
    return True


@_register(SupportScope.qq_guild)
async def select_qq_guild(target: "Target", bot: Bot):
    if bot.adapter.get_name() not in (SupportAdapter.onebot12, SupportAdapter.kritor):
        return False
    if not target.channel:
        return False
    if hasattr(bot, "platform") and bot.platform != "qqguild":
        return False
    return True


@_register(SupportScope.qq_api)
async def select_qq_api(target: "Target", bot: Bot):
    if bot.adapter.get_name() not in {SupportAdapter.qq, SupportAdapter.satori}:
        return False
    if hasattr(bot, "platform") and bot.platform != "qq":
        return False
    return True


@_register(SupportScope.onebot12_other)
async def select_onebot12_other(target: "Target", bot: Bot):
    return bot.adapter.get_name() == SupportAdapter.onebot12


@_register(SupportScope.satori_other)
async def select_satori_other(target: "Target", bot: Bot):
    return bot.adapter.get_name() == SupportAdapter.satori


@_register(SupportScope.telegram)
async def select_telegram(target: "Target", bot: Bot):
    if bot.adapter.get_name() not in {SupportAdapter.telegram, SupportAdapter.satori}:
        return False
    if hasattr(bot, "platform") and bot.platform != "telegram":
        return False
    return True


@_register(SupportScope.discord)
async def select_discord(target: "Target", bot: Bot):
    if not target.channel:
        return False
    if bot.adapter.get_name() not in {SupportAdapter.discord, SupportAdapter.satori, SupportAdapter.onebot12}:
        return False
    if hasattr(bot, "platform") and bot.platform != "discord":
        return False
    return True


@_register(SupportScope.feishu)
async def select_feishu(target: "Target", bot: Bot):
    if bot.adapter.get_name() not in {SupportAdapter.feishu, SupportAdapter.satori}:
        return False
    if hasattr(bot, "platform") and bot.platform != "feishu":
        return False
    return True


@_register(SupportScope.dodo)
async def select_dodo(target: "Target", bot: Bot):
    if not target.channel:
        return False
    return bot.adapter.get_name() == SupportAdapter.dodo


@_register(SupportScope.kook)
async def select_kook(target: "Target", bot: Bot):
    if not target.channel:
        return False
    if bot.adapter.get_name() not in {SupportAdapter.kook, SupportAdapter.satori, SupportAdapter.onebot12}:
        return False
    if hasattr(bot, "platform") and bot.platform not in ("kook", "kaiheila"):
        return False
    return True


@_register(SupportScope.minecraft)
async def select_minecraft(target: "Target", bot: Bot):
    if target.channel or target.private:
        return False
    return bot.adapter.get_name() == SupportAdapter.minecraft


@_register(SupportScope.github)
async def select_github(target: "Target", bot: Bot):
    if target.channel or target.private:
        return False
    return bot.adapter.get_name() == SupportAdapter.github


@_register(SupportScope.bilibili)
async def select_bilibili(target: "Target", bot: Bot):
    if target.channel or target.private:
        return False
    return bot.adapter.get_name() == SupportAdapter.bilibili


@_register(SupportScope.console)
async def select_console(target: "Target", bot: Bot):
    if target.channel:
        return False
    return bot.adapter.get_name() == SupportAdapter.console


@_register(SupportScope.ding)
async def select_ding(target: "Target", bot: Bot):
    if target.channel:
        return False
    if bot.adapter.get_name() not in {SupportAdapter.ding, SupportAdapter.satori}:
        return False
    if hasattr(bot, "platform") and bot.platform != "dingtalk":
        return False
    return True


@_register(SupportScope.wechat)
async def select_wechat(target: "Target", bot: Bot):
    if target.channel:
        return False
    if bot.adapter.get_name() != SupportAdapter.onebot12:
        return False
    if hasattr(bot, "platform") and bot.platform != "wechat":
        return False
    return True


@_register(SupportScope.wechat_oap)
async def select_wechat_oap(target: "Target", bot: Bot):
    if target.channel:
        return False
    if bot.adapter.get_name() != SupportAdapter.satori:
        return False
    if hasattr(bot, "platform") and bot.platform != "wechat-official":
        return False
    return True


@_register(SupportScope.wecom)
async def select_wecom(target: "Target", bot: Bot):
    if target.channel:
        return False
    if bot.adapter.get_name() != SupportAdapter.satori:
        return False
    if hasattr(bot, "platform") and bot.platform != "wecom":
        return False
    return True


@_register(SupportScope.tail_chat)
async def select_tailchat(target: "Target", bot: Bot):
    if not target.channel:
        return False
    if bot.adapter.get_name() not in {SupportAdapter.tail_chat}:
        return False
    return True
