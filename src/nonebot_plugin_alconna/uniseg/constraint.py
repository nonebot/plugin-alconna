from enum import Enum
from typing import Literal

from nonebot.utils import logger_wrapper

from .i18n import lang as lang  # noqa: F401

log = logger_wrapper("Plugin-Uniseg")


class SupportAdapter(str, Enum):
    """支持的适配器"""

    console = "Console"
    ding = "Ding"
    discord = "Discord"
    dodo = "DoDo"
    feishu = "Feishu"
    github = "GitHub"
    heybox = "Heybox"
    kritor = "Kritor"
    kook = "Kaiheila"
    mail = "Mail"
    minecraft = "Minecraft"
    mirai = "Mirai"
    ntchat = "ntchat"
    onebot11 = "OneBot V11"
    onebot12 = "OneBot V12"
    qq = "QQ"
    red = "RedProtocol"
    satori = "Satori"
    telegram = "Telegram"
    tail_chat = "Tailchat"
    wxmp = "WXMP"

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
    heybox = "Heybox"
    kook = "Kaiheila"
    mail = "Mail"
    minecraft = "Minecraft"
    github = "GitHub"
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
            "red": SupportScope.qq_client,
            "chronocat": SupportScope.qq_client,
            "onebot": SupportScope.qq_client,
            "nekobox": SupportScope.qq_client,
            "lagrange": SupportScope.qq_client,
            "lagrange.python": SupportScope.qq_client,
            "qq": SupportScope.qq_api,
            "qqguild": SupportScope.qq_api,
            "telegram": SupportScope.telegram,
            "discord": SupportScope.discord,
            "feishu": SupportScope.feishu,
            "wechat-official": SupportScope.wechat_oap,
            "wecom": SupportScope.wecom,
            "kook": SupportScope.kook,
            "dingtalk": SupportScope.ding,
            "mail": SupportScope.mail,
            "heybox": SupportScope.heybox,
        }.get(platform, SupportScope.satori_other)


class SupportAdapterModule(str, Enum):
    """支持的适配器的模块路径"""

    console = "nonebot.adapters.console"
    ding = "nonebot.adapters.ding"
    discord = "nonebot.adapters.discord"
    dodo = "nonebot.adapters.dodo"
    feishu = "nonebot.adapters.feishu"
    github = "nonebot.adapters.github"
    heybox = "nonebot.adapters.heybox"
    kritor = "nonebot.adapters.kritor"
    kook = "nonebot.adapters.kaiheila"
    mail = "nonebot.adapters.mail"
    minecraft = "nonebot.adapters.minecraft"
    mirai = "nonebot.adapters.mirai"
    ntchat = "nonebot.adapters.ntchat"
    onebot11 = "nonebot.adapters.onebot.v11"
    onebot12 = "nonebot.adapters.onebot.v12"
    qq = "nonebot.adapters.qq"
    red = "nonebot.adapters.red"
    satori = "nonebot.adapters.satori"
    telegram = "nonebot.adapters.telegram"
    tail_chat = "nonebot_adapter_tailchat"
    wxmp = "nonebot.adapters.wxmp"


UNISEG_MESSAGE: Literal["_alc_uniseg_message"] = "_alc_uniseg_message"
UNISEG_TARGET: Literal["_alc_uniseg_target"] = "_alc_uniseg_target"
UNISEG_MESSAGE_ID: Literal["_alc_uniseg_message_id"] = "_alc_uniseg_message_id"


class SerializeFailed(Exception): ...
