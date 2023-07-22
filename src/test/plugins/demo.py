# 应与使用的 adapter 对应
# 不加也可以，做了兼容
from typing import Literal

from tarina import lang
from importlib_metadata import distributions
from nonebot.adapters.onebot.v12.message import Message, MessageSegment
from arclet.alconna import (
    Args,
    Option,
    Alconna,
    Arparma,
    Subcommand,
    Duplication,
    SubcommandStub,
    namespace,
    command_manager,
)

import nonebot_plugin_alconna.adapters.onebot12  # noqa: F401
from nonebot_plugin_alconna import (
    Check,
    AlconnaMatches,
    AlconnaDuplication,
    assign,
    funcommand,
    on_alconna,
    set_output_converter,
)

set_output_converter(lambda t, x: Message([MessageSegment.text(x)]))

with namespace("nbtest") as ns:
    ns.headers = ["/"]
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
    pipcmd = on_alconna(
        pip, comp_config={"timeout": 10}, block=True
    )  # , auto_send_output=True)
    ali = on_alconna(
        Alconna(["/"], "一言"), aliases={"hitokoto"}, skip_for_unmatch=True
    )
    i18n = on_alconna(Alconna("lang", Args["lang", ["zh_CN", "en_US"]]))

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
    await help_cmd.send(MessageSegment.text(command_manager.all_command_help()))


@i18n.handle()
async def _i18n(arp: Arparma = AlconnaMatches()):
    try:
        lang.select(arp["lang"])
    except ValueError as e:
        await i18n.finish(str(e))
    await i18n.send("ok")


@pipcmd.handle([Check(assign("list"))])
async def pip_l():
    md = "\n".join([f"- {k} {v}" for k, v in get_dist_map().items()])
    await pipcmd.send(MessageSegment.text(md))


@pipcmd.handle([Check(assign("install.pak"))])
async def pip_i(res: PipResult = AlconnaDuplication(PipResult)):
    await pipcmd.send(f"pip installing {res.pak}...")


@pipcmd.handle()
async def pip_m():
    await pipcmd.send("WIP...")


@ali.handle()
async def yiyan(res: Arparma = AlconnaMatches()):
    if res.matched:
        await ali.send("WIP...")
    # else:
    #     await ali.send(f"[hitokoto] Unmatched: {res}")


table = {
    "add": float.__add__,
    "sub": float.__sub__,
    "mul": float.__mul__,
    "div": float.__truediv__,
}


@funcommand()
async def calc(op: Literal["add", "sub", "mul", "div"], a: float, b: float):
    """加法测试"""
    return f"{a} {op} {b} = {table[op](a, b)}"


@funcommand()
async def test(
    a: int,
    b: bool,
    *args: str,
    c: float = 1.0,
    d: int = 1,
    e: bool = False,
    **kwargs: str,
):
    """测试"""
    return (
        f"a: {a}\n"
        f"b: {b}\n"
        f"c: {c}\n"
        f"d: {d}\n"
        f"e: {e}\n"
        f"args: {args}\n"
        f"kwargs: {kwargs}\n"
    )
