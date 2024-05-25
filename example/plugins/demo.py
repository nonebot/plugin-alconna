from typing import Union, Literal

from tarina import lang
from nonebot import require
from nonebot.adapters.onebot.v12 import Bot
from importlib_metadata import distributions
from nonebot.adapters.onebot.v12.event import GroupMessageDeleteEvent
from arclet.alconna import (
    Args,
    Field,
    Option,
    Alconna,
    Arparma,
    MultiVar,
    Subcommand,
    CommandMeta,
    Duplication,
    SubcommandStub,
    namespace,
    store_true,
    command_manager,
)

require("nonebot_plugin_alconna")
require("nonebot_plugin_waiter")

from nonebot_plugin_waiter import waiter

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
    AlconnaArg,
    UniMessage,
    AlconnaMatch,
    AlconnaMatcher,
    UniversalSegment,
    assign,
    funcommand,
    on_alconna,
    image_fetch,
    add_global_extension,
    load_builtin_plugins,
)

load_builtin_plugins("echo", "lang", "help")


class DemoExtension(Extension):
    @property
    def priority(self) -> int:
        return 15

    @property
    def id(self) -> str:
        return "demo"

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

    test_cmd = on_alconna(Alconna("test", Args["target?", Union[str, At]]))

    pip = Alconna(
        "pip",
        Subcommand(
            "install",
            Args["pak#安装包的名字", str, Field(completion=lambda: "请输入安装包的名字")],
            Option("--upgrade", help_text="升级安装包"),
            Option("--force-reinstall", help_text="强制重新安装"),
        ),
        Subcommand("list", Option("--out-dated", help_text="列出过期的安装包"), help_text="列出安装包列表"),
        meta=CommandMeta(
            description="pip命令",
            usage="模拟pip命令",
            example="pip install nonebot\npip list [--out-dated]",
        ),
    )

    # auto_send already set in .env
    pipcmd = on_alconna(
        pip, comp_config={"tab": "切换", "enter": "确认", "exit": "退出", "timeout": 30}, block=True
    )  # , auto_send_output=True)
    i18n = on_alconna(Alconna("lang", Args["lang", ["zh_CN", "en_US"]]))
    login = on_alconna(
        Alconna(
            "login",
            Args["password?", str],
            Option("-r|--recall"),
        )
    )
    bind = on_alconna(Alconna("bind"))


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


ali = on_alconna(
    Alconna("一言"),
    aliases={"hitokoto"},
    skip_for_unmatch=True,
    use_cmd_start=True,
    use_origin=True,
)


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
async def func(
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


mask_cmd1 = on_alconna(
    Alconna(
        "设置词云形状1",
        Args["img?", Image],
        Option("--default", action=store_true, default=False),
    ),
)

mask_cmd1.shortcut(
    "设置默认词云形状1",
    {"command": "设置词云形状1", "args": ["--default"]},
)


@mask_cmd1.handle()
async def mask1_h(matcher: AlconnaMatcher, img: Match[Image]):
    if img.available:
        matcher.set_path_arg("img", img.result)


@mask_cmd1.got_path("img", prompt="请输入图片")
async def mask1_g(img: Image, default: Query[bool] = Query("default.value")):
    print(default)
    if default.result:
        await mask_cmd.send(img, fallback=True)
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
    @property
    def priority(self) -> int:
        return 14

    @property
    def id(self) -> str:
        return "test"

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
        message=await UniMessage(f"recalled {user_id} {message_id}").export(bot),  # type: ignore
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
        Option("add", Args["group_id", int]["name?", str]),
        Option("remove", Args["group_id", int]),
        Option("list"),
    ),
)


@group.assign("add", additional=permission_checker("group.add"))
async def group_add(name: Match[str]):
    if name.available:
        group.set_path_arg("add.name", name.result)


@group.got_path("add.name", prompt="请输入群名")
async def group_add_name(group_id: int, name: str = AlconnaArg("add.name")):
    await group.finish(f"add {group_id} {name}")


@group.assign("remove", additional=permission_checker("group.remove"))
async def group_remove(group_id: int):
    await group.finish(f"remove {group_id}")


@group.assign("list")
async def group_list():
    await group.finish("list")


test1_cmd = on_alconna(Alconna("test1", Args["target", Union[int, At]]), comp_config={})


@test1_cmd.handle()
async def tt1_h(target: Match[Union[int, At]]):
    res = target.result
    if isinstance(res, At):
        await test1_cmd.send(UniMessage(["ok\n", res]))
    else:
        await test1_cmd.send(UniMessage(f"ok {res}"))


statis = on_alconna(Alconna("statis"))


@statis.handle()
async def statis_h():
    cmds = command_manager.get_commands()
    sources = [cmd.meta.extra["matcher.source"] for cmd in cmds]
    await statis.finish(UniMessage(f"sources: {sources}"))


alc = Alconna(
    "添加教师",
    Args["name", str, Field(completion=lambda: "请输入姓名")],
    Args["phone", int, Field(completion=lambda: "请输入手机号")],
    Args["at", [str, At], Field(completion=lambda: "请输入教师号")],
    meta=CommandMeta(context_style="parentheses"),
)

cmd = on_alconna(alc, comp_config={"lite": True}, skip_for_unmatch=False)


@cmd.handle()
async def handle(name: str, phone: int, at: Union[str, At]):
    r = await UniMessage(f"姓名：{name}").send(reply_to=True)
    await r.reply(f"手机号：{phone}")
    await r.reply(f"教师号：{at!r}")
    await r.recall(delay=5)

    await cmd.send("请回复验证码：")

    @waiter(["message"], keep_session=True)
    async def receive(msg: UniMsg):
        return msg

    async for res in receive(timeout=10):
        if not res:
            await cmd.send("超时")
            return
        if str(res) == "123456":
            await cmd.send("验证成功")
            break
        await cmd.send("验证失败，请重新输入：")
        continue


hd = on_alconna(
    Alconna(
        "请求处理",
        Args["handle", ["-fa", "-fr", "-fi", "-ga", "-gr", "-gi"]]["id", str],
    )
)

hd.shortcut(
    r"dddd(\d+)",
    fuzzy=False,
    command="请求处理 -fa {0}",
)

hd.shortcut(
    "dddd",
    fuzzy=True,
    command="请求处理 -fa {%0}",
)


@hd.handle()
async def hd_h(handle: str, id: str):
    await hd.send(f"handle: {handle}\nid: {id}")


setu = on_alconna(
    Alconna(
        "setu",
        Args["count", int, 1],
        Option("r18", action=store_true, default=False, help_text="是否开启R18模式"),
        Option("tags", Args["tags", MultiVar(str, "*")], help_text="指定标签"),
    )
)


def wrapper(slot: Union[int, str], content: Union[str, None]):
    if slot == 0:
        if not content:
            return "1"
        if content == "点":
            import random

            return str(random.randint(1, 5))
    return content


setu.shortcut(
    r"(?:要|我要|给我|来|抽)(点|\d*)(?:张|个|份|幅)?(?:涩|色|瑟)图",
    command="setu {0} tags",
    fuzzy=True,
    wrapper=wrapper,
)

setu.shortcut(
    r"(?:要|我要|给我|来|抽)(点|\d*)(?:张|个|份|幅)?(.+?)的?(?:涩|色|瑟)图",
    command="setu {0}",
    arguments=["tags", "{1}"],
    fuzzy=True,
    wrapper=wrapper,
)


@setu.handle()
async def setu_h(count: int, tags: Match[tuple[str, ...]]):
    await setu.send(f"数量: {count}\n标签: {tags.result}")


class ReplyExtension(DemoExtension):
    @property
    def priority(self) -> int:
        return 14

    @property
    def id(self) -> str:
        return "reply"

    async def message_provider(self, event, state, bot: Bot, use_origin: bool = False):
        from nonebot_plugin_alconna.uniseg import reply_fetch

        try:
            msg = event.get_message()
        except ValueError:
            return
        if not (reply := await reply_fetch(event, bot)):
            return None
        uni_msg_reply = UniMessage()
        if reply.msg:
            reply_msg = reply.msg
            if isinstance(reply_msg, str):
                reply_msg = msg.__class__(reply_msg)
            uni_msg_reply = UniMessage.generate_without_reply(message=reply_msg, bot=bot)
        uni_msg = UniMessage.generate_without_reply(message=msg, bot=bot)
        uni_msg += " "
        uni_msg.extend(uni_msg_reply)
        return uni_msg


preview = on_alconna(
    Alconna(
        "preview",
        Args["content", str],
    ),
    extensions=[ReplyExtension],
)


@preview.handle()
async def preview_h(content: str):
    await preview.finish(f"rendering preview: {content}")
