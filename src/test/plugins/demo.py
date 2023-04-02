# 应与使用的 adapter 对应
# 不加也可以，做了兼容
import nonebot_plugin_alconna.adapters.console  # noqa
from arclet.alconna import Args, Arparma, Option, Subcommand, command_manager, namespace, Duplication, SubcommandStub, Empty
from arclet.alconna.tools import MarkdownTextFormatter
from importlib_metadata import distributions
from nonebot.adapters.console.message import Message, MessageSegment
from nonebot_plugin_alconna import Alconna, AlconnaMatches, on_alconna, set_output_converter, AlconnaDuplication

set_output_converter(lambda x: Message([MessageSegment.markdown(x)]))

with namespace("nbtest") as ns:
    ns.headers = ["/"]
    ns.formatter_type = MarkdownTextFormatter
    ns.builtin_option_name["help"] = {"-h", "帮助", "--help"}

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

    # auto_send already set in .env
    pipcmd = on_alconna(pip)  # , auto_send_output=True)
    ali = on_alconna(Alconna(["/"], "一言"), aliases={"hitokoto"}, skip_for_unmatch=False)

    class PipResult(Duplication):
        list: SubcommandStub
        pak: str


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
async def _help(arp: Arparma = AlconnaMatches()):
    await help_cmd.send(str(arp))
    await help_cmd.send(MessageSegment.markdown(command_manager.all_command_help()))


@pipcmd.handle()
async def ll(res: PipResult = AlconnaDuplication(PipResult)):
    if res.list.available:
        md = "\n".join([f"- {k} {v}" for k, v in get_dist_map().items()])
        await pipcmd.send(MessageSegment.markdown(md))
    elif res.pak != Empty:
        await pipcmd.send(f"pip installing {res.pak}...")


@ali.handle()
async def yiyan(res: Arparma = AlconnaMatches()):
    if res.matched:
        await ali.send("WIP...")
    else:
        await ali.send(f"[hitokoto] Unmatched: {res}")