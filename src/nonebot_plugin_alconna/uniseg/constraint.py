from enum import Enum


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
