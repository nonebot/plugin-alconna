from enum import Enum
from pathlib import Path

from tarina import lang
from nonebot.utils import logger_wrapper

lang.load(Path(__file__).parent / "i18n")
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
    kook = "Kaiheila"
    minecraft = "Minecraft"
    mirai = "mirai2"
    ntchat = "ntchat"
    onebot11 = "OneBot V11"
    onebot12 = "OneBot V12"
    qq = "QQ"
    red = "RedProtocol"
    satori = "Satori"
    telegram = "Telegram"
