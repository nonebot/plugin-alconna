from enum import Enum
from typing import Literal

from nonebot.utils import logger_wrapper

from .i18n import lang as lang  # noqa: F401

log = logger_wrapper("Plugin-Uniseg")


class SupportAdapter(str, Enum):
    """支持的适配器"""

    bilibili = "BilibiliLive"
    console = "Console"
    ding = "Ding"
    discord = "Discord"
    dodo = "DoDo"
    feishu = "Feishu"
    github = "GitHub"
    kritor = "Kritor"
    kook = "Kaiheila"
    minecraft = "Minecraft"
    mirai_official = "Mirai"
    mirai_community = "mirai2"
    ntchat = "ntchat"
    onebot11 = "OneBot V11"
    onebot12 = "OneBot V12"
    qq = "QQ"
    red = "RedProtocol"
    satori = "Satori"
    telegram = "Telegram"
    tail_chat = "Tailchat"

    nonebug = "fake"


class SupportScope(str, Enum):
    """支持的平台范围"""

    qq_client = "QQClient"
    """QQ 协议端"""
    qq_guild = "QQGuild"
    """QQ 用户频道，非官方接口"""
    qq_api = "QQAPI"
    """QQ 官方接口"""
    telegram = "Telegram"
    discord = "Discord"
    feishu = "Feishu"
    dodo = "DoDo"
    kook = "Kaiheila"
    minecraft = "Minecraft"
    github = "GitHub"
    bilibili = "Bilibili"
    console = "Console"
    ding = "Ding"
    wechat = "WeChat"
    """微信平台"""
    wechat_oap = "WeChatOfficialAccountPlatform"
    """微信公众号平台"""
    wecom = "WeCom"
    """企业微信平台"""
    tail_chat = "TailChat"
    """Tailchat平台"""

    onebot12_other = "Onebot12"
    """ob12 的其他平台"""
    satori_other = "satori"
    """satori 的其他平台"""

    @staticmethod
    def ensure_ob12(platform: str):
        return {
            "qq": SupportScope.qq_client,
            "qqguild": SupportScope.qq_guild,
            "discord": SupportScope.discord,
            "wechat": SupportScope.wechat,
            "kaiheila": SupportScope.kook,
        }.get(platform, SupportScope.onebot12_other)

    @staticmethod
    def ensure_satori(platform: str):
        return {
            "chronocat": SupportScope.qq_client,
            "onebot": SupportScope.qq_client,
            "qq": SupportScope.qq_guild,
            "telegram": SupportScope.telegram,
            "discord": SupportScope.discord,
            "feishu": SupportScope.feishu,
            "wechat-official": SupportScope.wechat_oap,
            "wecom": SupportScope.wecom,
            "kook": SupportScope.kook,
            "dingtalk": SupportScope.ding,
        }.get(platform, SupportScope.satori_other)


class SupportAdapterModule(str, Enum):
    """支持的适配器的模块路径"""

    bilibili = "nonebot.adapters.bilibili"
    console = "nonebot.adapters.console"
    ding = "nonebot.adapters.ding"
    discord = "nonebot.adapters.discord"
    dodo = "nonebot.adapters.dodo"
    feishu = "nonebot.adapters.feishu"
    github = "nonebot.adapters.github"
    kritor = "nonebot.adapters.kritor"
    kook = "nonebot.adapters.kaiheila"
    minecraft = "nonebot.adapters.minecraft"
    mirai_official = "nonebot.adapters.mirai"
    mirai_community = "nonebot.adapters.mirai2"
    ntchat = "nonebot.adapters.ntchat"
    onebot11 = "nonebot.adapters.onebot.v11"
    onebot12 = "nonebot.adapters.onebot.v12"
    qq = "nonebot.adapters.qq"
    red = "nonebot.adapters.red"
    satori = "nonebot.adapters.satori"
    telegram = "nonebot.adapters.telegram"
    tail_chat = "nonebot_adapter_tailchat"


UNISEG_MESSAGE: Literal["_alc_uniseg_message"] = "_alc_uniseg_message"
UNISEG_TARGET: Literal["_alc_uniseg_target"] = "_alc_uniseg_target"
UNISEG_MESSAGE_ID: Literal["_alc_uniseg_message_id"] = "_alc_uniseg_message_id"


class SerializeFailed(Exception): ...
