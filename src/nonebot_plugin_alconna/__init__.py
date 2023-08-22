import contextlib

from nonebot import get_driver
from arclet.alconna import Args as Args
from arclet.alconna import Field as Field
from arclet.alconna import count as count
from nonebot.plugin import PluginMetadata
from arclet.alconna import Option as Option
from arclet.alconna import append as append
from arclet.alconna import config as config
from arclet.alconna import Alconna as Alconna
from arclet.alconna import Arparma as Arparma
from arclet.alconna import ArgsStub as ArgsStub
from arclet.alconna import MultiVar as MultiVar
from nonebot.internal.params import DefaultParam
from arclet.alconna import Namespace as Namespace
from arclet.alconna import namespace as namespace
from nonebot import __version__ as nonebot_version
from arclet.alconna import KeyWordVar as KeyWordVar
from arclet.alconna import OptionStub as OptionStub
from arclet.alconna import Subcommand as Subcommand
from arclet.alconna import store_true as store_true
from arclet.alconna import CommandMeta as CommandMeta
from arclet.alconna import Duplication as Duplication
from arclet.alconna import store_false as store_false
from arclet.alconna import store_value as store_value
from arclet.alconna import OptionResult as OptionResult
from arclet.alconna import append_value as append_value
from arclet.alconna import SubcommandStub as SubcommandStub
from arclet.alconna import output_manager as output_manager
from arclet.alconna import command_manager as command_manager
from arclet.alconna import SubcommandResult as SubcommandResult

from .config import Config
from .adapters import At as At
from .model import Match as Match
from .model import Query as Query
from .adapters import File as File
from .params import Check as Check
from .adapters import AtAll as AtAll
from .adapters import Audio as Audio
from .adapters import Emoji as Emoji
from .adapters import Image as Image
from .adapters import Reply as Reply
from .adapters import Video as Video
from .adapters import Voice as Voice
from .params import SegMsg as SegMsg
from .params import assign as assign
from .rule import alconna as alconna
from .matcher import Command as Command
from .adapters import Segment as Segment
from .rule import seg_match as seg_match
from .params import AlcResult as AlcResult
from .argv import MessageArgv as MessageArgv
from .params import AlcMatches as AlcMatches
from .params import AlconnaArg as AlconnaArg
from .params import match_path as match_path
from .matcher import funcommand as funcommand
from .matcher import on_alconna as on_alconna
from .tools import image_fetch as image_fetch
from .params import match_value as match_value
from .tools import reply_handle as reply_handle
from .consts import SEGMATCH_MSG as SEGMATCH_MSG
from .params import AlconnaMatch as AlconnaMatch
from .params import AlconnaParam as AlconnaParam
from .params import AlconnaQuery as AlconnaQuery
from .model import CommandResult as CommandResult
from .params import AlcExecResult as AlcExecResult
from .params import AlconnaResult as AlconnaResult
from .consts import ALCONNA_RESULT as ALCONNA_RESULT
from .params import AlconnaMatches as AlconnaMatches
from .params import SegMatchResult as SegMatchResult
from .matcher import AlconnaMatcher as AlconnaMatcher
from .consts import ALCONNA_ARG_KEY as ALCONNA_ARG_KEY
from .consts import SEGMATCH_RESULT as SEGMATCH_RESULT
from .params import SegMatchMessage as SegMatchMessage
from .params import AlconnaExecResult as AlconnaExecResult
from .params import AlconnaDuplication as AlconnaDuplication
from .consts import ALCONNA_EXEC_RESULT as ALCONNA_EXEC_RESULT
from .rule import set_output_converter as set_output_converter

__version__ = "0.17.0"

_meta_source = {
    "name": "Alconna 插件",
    "description": "提供 ArcletProject/Alconna 的 Nonebot2 适配版本与工具",
    "usage": "matcher = on_alconna(...)",
    "homepage": "https://github.com/nonebot/plugin-alconna",
    "type": "library",
    "supported_adapters": None,
    "config": Config,
    "extra": {
        "author": "RF-Tar-Railt",
        "priority": 1,
        "version": __version__,
    },
}


if not nonebot_version.split(".")[-1].isdigit():
    _meta_source["extra"]["homepage"] = _meta_source.pop("homepage")
    _meta_source["extra"]["type"] = _meta_source.pop("type")
    _meta_source["extra"]["config"] = _meta_source.pop("config")
    _meta_source["extra"]["supported_adapters"] = _meta_source.pop("supported_adapters")


__plugin_meta__ = PluginMetadata(**_meta_source)

with contextlib.suppress(ValueError, LookupError):
    global_config = get_driver().config
    _config = Config.parse_obj(global_config)
    if _config.alconna_use_param:
        AlconnaMatcher.HANDLER_PARAM_TYPES = (
            *AlconnaMatcher.HANDLER_PARAM_TYPES[:-1],
            AlconnaParam,
            DefaultParam,
        )
