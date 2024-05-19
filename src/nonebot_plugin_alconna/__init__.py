import contextlib

import nonebot

nonebot.load_plugin("nonebot_plugin_alconna.uniseg")

from tarina import lang
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
from nonebot import load_plugin, load_all_plugins, get_plugin_config

from .consts import log
from .config import Config
from .uniseg import At as At
from . import pattern as pattern
from .uniseg import File as File
from .uniseg import Text as Text
from .model import Match as Match
from .model import Query as Query
from .typings import AtID as AtID
from .typings import Bold as Bold
from .typings import Code as Code
from .params import Check as Check
from .uniseg import AtAll as AtAll
from .uniseg import Audio as Audio
from .uniseg import Emoji as Emoji
from .uniseg import Hyper as Hyper
from .uniseg import Image as Image
from .uniseg import MsgId as MsgId
from .uniseg import Other as Other
from .uniseg import Reply as Reply
from .uniseg import Video as Video
from .uniseg import Voice as Voice
from .typings import Style as Style
from .params import assign as assign
from .rule import alconna as alconna
from .uniseg import SCOPES as SCOPES
from .uniseg import Target as Target
from .uniseg import UniMsg as UniMsg
from .pattern import select as select
from .typings import Italic as Italic
from .uniseg import RefNode as RefNode
from .uniseg import Segment as Segment
from .uniseg import get_bot as get_bot
from .matcher import Command as Command
from .typings import Spoiler as Spoiler
from .matcher import referent as referent
from .params import AlcResult as AlcResult
from .uniseg import MessageId as MessageId
from .uniseg import MsgTarget as MsgTarget
from .uniseg import Reference as Reference
from .uniseg import patch_saa as patch_saa
from .typings import Underline as Underline
from .argv import MessageArgv as MessageArgv
from .params import AlcContext as AlcContext
from .params import AlcMatches as AlcMatches
from .params import AlconnaArg as AlconnaArg
from .params import match_path as match_path
from .uniseg import CustomNode as CustomNode
from .uniseg import UniMessage as UniMessage
from .extension import Extension as Extension
from .extension import Interface as Interface
from .matcher import funcommand as funcommand
from .matcher import on_alconna as on_alconna
from .typings import ImageOrUrl as ImageOrUrl
from .params import match_value as match_value
from .uniseg import image_fetch as image_fetch
from .pattern import select_last as select_last
from .params import AlconnaMatch as AlconnaMatch
from .params import AlconnaQuery as AlconnaQuery
from .uniseg import SupportScope as SupportScope
from .model import CommandResult as CommandResult
from .pattern import select_first as select_first
from .params import AlcExecResult as AlcExecResult
from .params import AlconnaResult as AlconnaResult
from .uniseg import MessageTarget as MessageTarget
from .typings import Strikethrough as Strikethrough
from .consts import ALCONNA_RESULT as ALCONNA_RESULT
from .params import AlconnaContext as AlconnaContext
from .params import AlconnaMatches as AlconnaMatches
from .uniseg import SupportAdapter as SupportAdapter
from .uniseg import apply_filehost as apply_filehost
from .uniseg import custom_handler as custom_handler
from .matcher import AlconnaMatcher as AlconnaMatcher
from .consts import ALCONNA_ARG_KEY as ALCONNA_ARG_KEY
from .uniseg import SerializeFailed as SerializeFailed
from .uniseg import custom_register as custom_register
from .extension import load_from_path as load_from_path
from .uniseg import UniversalMessage as UniversalMessage
from .uniseg import UniversalSegment as UniversalSegment
from .params import AlconnaExecResult as AlconnaExecResult
from .params import AlconnaDuplication as AlconnaDuplication
from .uniseg import apply_media_to_url as apply_media_to_url
from .consts import ALCONNA_EXEC_RESULT as ALCONNA_EXEC_RESULT
from .uniseg import apply_fetch_targets as apply_fetch_targets
from .uniseg import SupportAdapterModule as SupportAdapterModule
from .extension import add_global_extension as add_global_extension

__version__ = "0.46.0"

__plugin_meta__ = PluginMetadata(
    name="Alconna 插件",
    description="提供 ArcletProject/Alconna 的 Nonebot2 适配版本与工具",
    usage="matcher = on_alconna(...)",
    homepage="https://github.com/nonebot/plugin-alconna",
    type="library",
    supported_adapters=set(SupportAdapterModule.__members__.values()),
    config=Config,
    extra={
        "author": "RF-Tar-Railt",
        "priority": 1,
        "version": __version__,
    },
)

with contextlib.suppress(ValueError, LookupError):
    _config = get_plugin_config(Config)
    for path in _config.alconna_global_extensions:
        log("DEBUG", lang.require("nbp-alc", "log.load_global_extensions").format(path=path))
        load_from_path(path)
    if _config.alconna_apply_filehost:
        apply_filehost()
    if _config.alconna_enable_saa_patch:
        patch_saa()
    if _config.alconna_apply_fetch_targets:
        apply_fetch_targets()


def load_builtin_plugin(name: str):
    """导入 Nonebot Plugin Alconna 内置插件。

    参数:
        name: 插件名称
    """
    return load_plugin(f"nonebot_plugin_alconna.builtins.plugins.{name}")


def load_builtin_plugins(*plugins: str):
    """导入多个 Nonebot Plugin Alconna 内置插件。

    参数:
        plugins: 插件名称列表
    """
    return load_all_plugins([f"nonebot_plugin_alconna.builtins.plugins.{p}" for p in plugins], [])
