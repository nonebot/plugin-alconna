import contextlib

import nonebot

nonebot.load_plugin("nonebot_plugin_alconna.uniseg")

from tarina import lang
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
from arclet.alconna import Namespace as Namespace
from arclet.alconna import namespace as namespace
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
from arclet.alconna import ArparmaBehavior as ArparmaBehavior
from arclet.alconna import command_manager as command_manager
from arclet.alconna import SubcommandResult as SubcommandResult

from .consts import log
from .config import Config
from .uniseg import At as At
from .uniseg import Card as Card
from .uniseg import File as File
from .uniseg import Text as Text
from .model import Match as Match
from .model import Query as Query
from .params import Check as Check
from .uniseg import AtAll as AtAll
from .uniseg import Audio as Audio
from .uniseg import Emoji as Emoji
from .uniseg import Image as Image
from .uniseg import MsgId as MsgId
from .uniseg import Other as Other
from .uniseg import Reply as Reply
from .uniseg import Video as Video
from .uniseg import Voice as Voice
from .params import assign as assign
from .rule import alconna as alconna
from .uniseg import Target as Target
from .uniseg import UniMsg as UniMsg
from .uniseg import RefNode as RefNode
from .uniseg import Segment as Segment
from .uniseg import get_bot as get_bot
from .matcher import Command as Command
from .matcher import referent as referent
from .params import AlcResult as AlcResult
from .uniseg import MessageId as MessageId
from .uniseg import MsgTarget as MsgTarget
from .uniseg import Reference as Reference
from .argv import MessageArgv as MessageArgv
from .params import AlcMatches as AlcMatches
from .params import AlconnaArg as AlconnaArg
from .params import match_path as match_path
from .uniseg import CustomNode as CustomNode
from .uniseg import UniMessage as UniMessage
from .extension import Extension as Extension
from .extension import Interface as Interface
from .matcher import funcommand as funcommand
from .matcher import on_alconna as on_alconna
from .params import match_value as match_value
from .uniseg import image_fetch as image_fetch
from .params import AlconnaMatch as AlconnaMatch
from .params import AlconnaQuery as AlconnaQuery
from .model import CommandResult as CommandResult
from .params import AlcExecResult as AlcExecResult
from .params import AlconnaResult as AlconnaResult
from .uniseg import MessageTarget as MessageTarget
from .consts import ALCONNA_RESULT as ALCONNA_RESULT
from .params import AlconnaMatches as AlconnaMatches
from .matcher import AlconnaMatcher as AlconnaMatcher
from .consts import ALCONNA_ARG_KEY as ALCONNA_ARG_KEY
from .uniseg import SerializeFailed as SerializeFailed
from .extension import load_from_path as load_from_path
from .uniseg import UniversalMessage as UniversalMessage
from .uniseg import UniversalSegment as UniversalSegment
from .params import AlconnaExecResult as AlconnaExecResult
from .params import AlconnaDuplication as AlconnaDuplication
from .consts import ALCONNA_EXEC_RESULT as ALCONNA_EXEC_RESULT
from .extension import add_global_extension as add_global_extension

__version__ = "0.33.8"

__plugin_meta__ = PluginMetadata(
    name="Alconna 插件",
    description="提供 ArcletProject/Alconna 的 Nonebot2 适配版本与工具",
    usage="matcher = on_alconna(...)",
    homepage="https://github.com/nonebot/plugin-alconna",
    type="library",
    supported_adapters=None,
    config=Config,
    extra={
        "author": "RF-Tar-Railt",
        "priority": 1,
        "version": __version__,
    },
)

with contextlib.suppress(ValueError, LookupError):
    global_config = get_driver().config
    _config = Config.parse_obj(global_config)
    for path in _config.alconna_global_extensions:
        log("DEBUG", lang.require("nbp-alc", "log.load_global_extensions").format(path=path))
        load_from_path(path)
