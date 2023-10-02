from typing import Union, Literal

from tarina import lang
from nonebot import require
from nonebot.adapters.onebot.v12 import Bot
from importlib_metadata import distributions
from nonebot.adapters.onebot.v12.event import GroupMessageDeleteEvent
from arclet.alconna import (
    Args,
    Option,
    Alconna,
    Arparma,
    Subcommand,
    Duplication,
    SubcommandStub,
    namespace,
    store_true,
    command_manager,
)

require("nonebot_plugin_alconna")

from nonebot_plugin_alconna import (
    At,
    Check,
    Image,
    Match,
    Query,
    Reply,
    UniMsg,
    Command,
    Extension,
    UniMessage,
    AlconnaMatch,
    AlconnaMatcher,
    UniversalSegment,
    assign,
    funcommand,
    on_alconna,
    image_fetch,
    add_global_extension,
)


class DemoExtension(Extension):
    priority = 15

    async def output_converter(self, output_type, content: str):
        return UniMessage(content)


add_global_extension(DemoExtension())


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


class PipResult(Duplication):
    list: SubcommandStub
    pak: str


with namespace("nbtest") as ns:
    ns.headers = ["/"]
    ns.builtin_option_name["help"] = {"-h", "帮助", "--help"}

    help_cmd = on_alconna(Alconna("help"))
    test_cmd = on_alconna(Alconna("test", Args["target?", Union[str, At]]))

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
    pipcmd = on_alconna(pip, comp_config={"timeout": 10}, block=True)  # , auto_send_output=True)
    ali = on_alconna(
        Alconna(["/"], "一言"),
        aliases={"hitokoto"},
        skip_for_unmatch=True,
        use_origin=True,
    )
    i18n = on_alconna(Alconna("lang", Args["lang", ["zh_CN", "en_US"]]))
    login = on_alconna(
        Alconna(
            "login",
            Args["password?", str],
            Option("-r|--recall"),
        )
    )
    bind = on_alconna(Alconna("bind"))


@help_cmd.handle()
async def _help():
    await help_cmd.send(UniMessage(command_manager.all_command_help()))


@i18n.handle()
async def _i18n(arp: Arparma):
    try:
        lang.select(arp["lang"])
    except ValueError as e:
        await i18n.finish(str(e))
    await i18n.send("ok")


@pipcmd.handle([Check(assign("list"))])
async def pip_l():
    md = "\n".join([f"- {k} {v}" for k, v in get_dist_map().items()])
    await pipcmd.send(UniMessage(md))


@pipcmd.assign("install.pak")
async def pip_i(res: PipResult):
    await pipcmd.send(f"pip installing {res.pak}...")


@pipcmd.handle()
async def pip_m():
    await pipcmd.send("WIP...")


@ali.handle()
async def yiyan(res: Arparma):
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
    return f"a: {a}\n" f"b: {b}\n" f"c: {c}\n" f"d: {d}\n" f"e: {e}\n" f"args: {args}\n" f"kwargs: {kwargs}\n"


@test_cmd.handle()
async def tt_h(matcher: AlconnaMatcher, target: Match[Union[str, At]]):
    if target.available:
        matcher.set_path_arg("target", target.result)


@test_cmd.got_path("target", prompt="请输入目标")
async def tt(target: Union[str, At]):
    await test_cmd.send(UniMessage(["ok\n", target]))


@login.assign("recall")
async def login_exit():
    await login.finish("已退出")


@login.handle()
async def login_handle():
    await login.send(UniMessage.template("{:At(user,$event.get_user_id())}, login success"))


@bind.handle()
async def bind_handle(unimsg: UniMsg, _reply: Reply = UniversalSegment(Reply)):
    if unimsg.has(Reply):
        reply = unimsg[Reply, 0]
        await bind.send(repr(unimsg))
        await bind.send(repr(reply) + "\n" + repr(_reply))


mask_cmd = on_alconna(
    Alconna(
        "设置词云形状",
        Args["img?", Image],
        Option("--default", action=store_true, default=False),
    ),
)

mask_cmd.shortcut(
    "设置默认词云形状",
    {"command": "设置词云形状", "args": ["--default"]},
)


@mask_cmd.handle()
async def mask_h(matcher: AlconnaMatcher, img: Match[bytes] = AlconnaMatch("img", image_fetch)):
    if img.available:
        matcher.set_path_arg("img", img.result)


@mask_cmd.got_path("img", prompt="请输入图片", middleware=image_fetch)
async def mask_g(img: bytes, default: Query[bool] = Query("default.value")):
    print(default)
    if default.result:
        await mask_cmd.send(Image(raw=img), fallback=True)
    else:
        await mask_cmd.send("ok")


book = (
    Command("book", "测试")
    .option("writer", "-w <id:int>")
    .option("writer", "--anonymous", {"id": 0})
    .usage("book [-w <id:int> | --anonymous]")
    .shortcut("测试", {"args": ["--anonymous"]})
    .action(lambda options: str(options))
    .build()
)

pip1 = Alconna(
    "pip1",
    Subcommand(
        "install",
        Args["pak", str],
        Option("--upgrade|-U"),
        Option("--force-reinstall"),
    ),
    Subcommand("list", Option("--out-dated")),
)

pipcmd1 = on_alconna(pip1)

pip_list_cmd = pipcmd1.dispatch("list")
pip_install_cmd = pipcmd1.dispatch("install")


@pip_list_cmd.handle()
async def pip1_l():
    md = "\n".join([f"- {k} {v}" for k, v in get_dist_map().items()])
    await pipcmd1.finish(UniMessage(md))


@pip_install_cmd.assign("~upgrade")
async def pip1_u(pak: Query[str] = Query("~pak")):
    await pip_install_cmd.finish(f"pip upgrading {pak.result}...")


@pip_install_cmd.handle()
async def pip1_i(res: PipResult):
    await pipcmd1.finish(f"pip installing {res.pak}...")


@pipcmd1.handle()
async def pip1_m():
    await pipcmd1.send("WIP...")


class TestExtension(DemoExtension):
    priority = 14

    async def message_provider(self, event, state, bot: Bot, use_origin: bool = False):
        if not isinstance(event, GroupMessageDeleteEvent):
            return None
        return UniMessage(f"/recall {str(event.group_id)} {str(event.user_id)} {str(event.message_id)}")


recall = on_alconna(
    Alconna(
        "/recall",
        Args["group_id", str]["user_id", str]["message_id", int],
    ),
    extensions=[TestExtension],
)


@recall.handle()
async def recall_h(group_id: str, user_id: str, message_id: str, bot: Bot):
    await bot.send_message(
        detail_type="group",
        user_id=user_id,
        group_id=group_id,
        message=await UniMessage(f"recalled {user_id} {message_id}").export(bot),
    )


def permission_checker(permission: str):
    import random

    async def wrapper(event, bot, state, arp):
        if random.random() < 0.5:
            await bot.send(event, "permission denied")
            return False
        return True

    return wrapper


group = on_alconna(
    Alconna(
        "group",
        Option("add", Args["group_id", int]["name", str]),
        Option("remove", Args["group_id", int]),
        Option("list"),
    ),
)


@group.assign("add", additional=permission_checker("group.add"))
async def group_add(group_id: int, name: str):
    await group.finish(f"add {group_id} {name}")


@group.assign("remove", additional=permission_checker("group.remove"))
async def group_remove(group_id: int):
    await group.finish(f"remove {group_id}")


@group.assign("list")
async def group_list():
    await group.finish("list")
