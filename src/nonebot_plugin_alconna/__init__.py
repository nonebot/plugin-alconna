from .consts import ALCONNA_RESULT as ALCONNA_RESULT
from .matcher import on_alconna as on_alconna
from .model import CommandResult as CommandResult
from .model import Match as Match
from .model import Query as Query
from .params import AlcMatches as AlcMatches
from .params import AlconnaDuplication as AlconnaDuplication
from .params import AlconnaMatch as AlconnaMatch
from .params import AlconnaMatches as AlconnaMatches
from .params import AlconnaQuery as AlconnaQuery
from .params import AlconnaResult as AlconnaResult
from .params import AlcResult as AlcResult
from .params import assign as assign
from .params import match_path as match_path
from .params import match_value as match_value
from .params import Check as Check
from .rule import alconna as alconna
from .rule import set_output_converter as set_output_converter
from .argv import MessageArgv as MessageArgv

from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="Alconna 插件",
    description="提供 [Alconna](https://github.com/ArcletProject/Alconna) 的 Nonebot2 适配版本与工具",
    usage="matcher = on_alconna(...)",
    extra={
        "author": "RF-Tar-Railt",
        'priority': 16,
    }
)