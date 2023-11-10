from typing import Dict

from ..export import MessageExporter
from .qq import QQMessageExporter  # noqa: F401
from .red import RedMessageExporter  # noqa: F401
from .ding import DingMessageExporter  # noqa: F401
from .dodo import DoDoMessageExporter  # noqa: F401
from .kook import KookMessageExporter  # noqa: F401
from .mirai import MiraiMessageExporter  # noqa: F401
from .villa import VillaMessageExporter  # noqa: F401
from .feishu import FeishuMessageExporter  # noqa: F401
from .github import GithubMessageExporter  # noqa: F401
from .ntchat import NTChatMessageExporter  # noqa: F401
from .satori import SatoriMessageExporter  # noqa: F401
from .console import ConsoleMessageExporter  # noqa: F401
from .discord import DiscordMessageExporter  # noqa: F401
from .qqguild import QQGuildMessageExporter  # noqa: F401
from .bilibili import BilibiliMessageExporter  # noqa: F401
from .onebot11 import Onebot11MessageExporter  # noqa: F401
from .onebot12 import Onebot12MessageExporter  # noqa: F401
from .telegram import TelegramMessageExporter  # noqa: F401
from .minecraft import MinecraftMessageExporter  # noqa: F401

MAPPING: Dict[str, MessageExporter] = {cls.get_adapter(): cls() for cls in MessageExporter.__subclasses__()}
