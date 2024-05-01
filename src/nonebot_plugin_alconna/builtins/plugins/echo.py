from nonebot.plugin import PluginMetadata
from arclet.alconna import Args, Alconna, AllParam, CommandMeta, namespace

from nonebot_plugin_alconna import UniMessage, on_alconna

__plugin_meta__ = PluginMetadata(
    name="echo",
    description="重复你说的话",
    usage="/echo [text]",
    type="application",
    homepage="https://github.com/nonebot/plugin-alconna/blob/master/src/nonebot_plugin_alconna/builtins/plugins/echo.py",
    config=None,
    supported_adapters=None,
)

with namespace("builtin/echo") as ns:
    ns.disable_builtin_options = {"shortcut", "completion"}

    echo = on_alconna(
        Alconna("echo", Args["content", AllParam], meta=CommandMeta("echo 指令", usage="重复你说的话", compact=True)),
        auto_send_output=True,
        use_cmd_start=True,
    )


@echo.handle()
async def handle_echo(content: UniMessage):
    await echo.send(content)
