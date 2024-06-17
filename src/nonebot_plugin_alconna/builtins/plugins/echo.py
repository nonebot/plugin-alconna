from arclet.alconna import namespace
from nonebot.plugin import PluginMetadata, inherit_supported_adapters

from nonebot_plugin_alconna import Command
from nonebot_plugin_alconna.builtins.extensions.reply import ReplyMergeExtension

__plugin_meta__ = PluginMetadata(
    name="echo",
    description="重复你说的话",
    usage="/echo [text]",
    type="application",
    homepage="https://github.com/nonebot/plugin-alconna/blob/master/src/nonebot_plugin_alconna/builtins/plugins/echo.py",
    config=None,
    supported_adapters=inherit_supported_adapters("nonebot_plugin_alconna"),
)

with namespace("builtin/echo") as ns:
    ns.disable_builtin_options = {"shortcut", "completion"}

    echo = (
        Command("echo <...content>", "echo 指令")
        .config(compact=True)
        .usage("重复你说的话")
        .action(lambda content: content)
        .build(auto_send_output=True, use_cmd_start=True, extensions=[ReplyMergeExtension()])
    )
