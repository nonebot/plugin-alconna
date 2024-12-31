from nonebot.rule import to_me
from arclet.alconna import namespace
from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata

from nonebot_plugin_alconna import Command, __supported_adapters__
from nonebot_plugin_alconna.builtins.extensions.reply import ReplyMergeExtension

from .config import Config

plugin_config = get_plugin_config(Config)

__plugin_meta__ = PluginMetadata(
    name="echo",
    description="重复你说的话",
    usage="/echo [text]",
    type="application",
    homepage="https://github.com/nonebot/plugin-alconna/blob/master/src/nonebot_plugin_alconna/builtins/plugins/echo",
    config=Config,
    supported_adapters=__supported_adapters__,
)

with namespace("builtin/echo") as ns:
    ns.disable_builtin_options = {"shortcut", "completion"}

    echo = (
        Command("echo <...content>", "echo 指令")
        .config(compact=True)
        .usage("重复你说的话")
        .action(lambda content: content)
        .build(
            use_cmd_start=True,
            extensions=[ReplyMergeExtension()],
            rule=to_me() if plugin_config.nbp_alc_echo_tome else None,
        )
    )
