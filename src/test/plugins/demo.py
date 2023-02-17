# 应与使用的 adapter 对应
# 不加也可以，做了兼容
import nonebot_plugin_alconna.adapters.console  # noqa
from arclet.alconna import Args, Arparma, Option, Subcommand, command_manager, namespace
from arclet.alconna.tools import MarkdownTextFormatter
from importlib_metadata import distributions
from nonebot.adapters.console.message import Message, MessageSegment
from nonebot_plugin_alconna import Alconna, AlconnaMatches, on_alconna, set_converter

set_converter(lambda x: Message([MessageSegment.markdown(x)]))

with namespace("nbtest") as ns:
    ns.headers = ["/"]
    ns.formatter_type = MarkdownTextFormatter

    help_cmd = on_alconna(Alconna("help"))

    pip = Alconna(
        "pip",
        Subcommand(
            "install",
            Args["pak", str],
            Option("--upgrade"),
            Option("--force-reinstall"),
        ),
        Subcommand("list", Option("--out-dated")),
    )

    pipcmd = on_alconna(pip, auto_send_output=True)


def get_dist_map() -> dict:
    """获取与项目相关的发行字典"""
    dist_map: dict = {}
    for dist in distributions():
        name: str = dist.metadata["Name"]
        version: str = dist.metadata["Version"]
        if not name or not version:
            continue
        dist_map[name] = max(version, dist_map.get(name, ""))
    return dist_map


@help_cmd.handle()
async def _help():
    await help_cmd.send(MessageSegment.markdown(command_manager.all_command_help()))


@pipcmd.handle()
async def res(arp: Arparma = AlconnaMatches()):
    if arp.components.get("list"):
        md = "\n".join([f"- {k} {v}" for k, v in get_dist_map().items()])
        await pipcmd.send(MessageSegment.markdown(md))
    else:
        await pipcmd.send(str(arp))
