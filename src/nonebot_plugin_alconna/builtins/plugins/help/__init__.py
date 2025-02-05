import sys
import random
from pathlib import Path

from tarina import lang
from nonebot.adapters import Bot
from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata
from importlib_metadata import PackageNotFoundError, distribution
from arclet.alconna import (
    Args,
    Field,
    Option,
    Alconna,
    Arparma,
    Subcommand,
    CommandMeta,
    SubcommandResult,
    namespace,
    store_true,
    command_manager,
)

from nonebot_plugin_alconna import UniMessage, AlconnaMatcher, referent, on_alconna, __supported_adapters__

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="help",
    description="展示所有命令帮助",
    usage="/help",
    type="application",
    homepage="https://github.com/nonebot/plugin-alconna/blob/master/src/nonebot_plugin_alconna/builtins/plugins/help",
    config=Config,
    supported_adapters=__supported_adapters__,
)


plugin_config = get_plugin_config(Config)


def check_supported_adapters(matcher: type[AlconnaMatcher], bot: Bot):
    if matcher.plugin and matcher.plugin.metadata:
        adapters = matcher.plugin.metadata.supported_adapters
        if adapters is None:
            return True
        if not adapters:
            return False
        adapters = {s.replace("~", "nonebot.adapters") for s in adapters}
        return bot.adapter.__module__.removesuffix(".adapter") in adapters
    return True


def get_info(matcher: type[AlconnaMatcher]):
    if matcher.plugin:
        if matcher.plugin.metadata:
            plugin_name = matcher.plugin.metadata.name
        else:
            plugin_name = matcher.plugin.name
    else:
        plugin_name = matcher.plugin_id or lang.require("nbp-alc/builtin", "help.plugin_name_unknown")
    plugin_id = matcher.plugin_id or lang.require("nbp-alc/builtin", "help.plugin_name_unknown")
    mod = matcher.module or sys.modules["__main__"]
    mod_path = Path(mod.__file__)  # type: ignore
    while mod_path.parent != mod_path:
        try:
            dist = distribution(mod_path.name)
            break
        except PackageNotFoundError:
            mod_path = mod_path.parent
    else:
        return f"""\
{lang.require("nbp-alc/builtin", "help.plugin_name")}: {plugin_name}
{lang.require("nbp-alc/builtin", "help.plugin_id")}: {plugin_id}
{lang.require("nbp-alc/builtin", "help.plugin_path")}: {matcher.module_name}
"""
    return f"""\
{lang.require("nbp-alc/builtin", "help.plugin_name")}: {plugin_name}
{lang.require("nbp-alc/builtin", "help.plugin_id")}: {plugin_id}
{lang.require("nbp-alc/builtin", "help.plugin_module")}: {dist.name}
{lang.require("nbp-alc/builtin", "help.plugin_version")}: {dist.version}
{lang.require("nbp-alc/builtin", "help.plugin_path")}: {matcher.module_name}
"""


with namespace("builtin/help") as ns:
    ns.disable_builtin_options = {"shortcut"}

    help_cmd = Alconna(
        plugin_config.nbp_alc_help_text,
        Args[
            "query#选择某条命令的id或者名称查看具体帮助;/?",
            str,
            Field(
                "-1",
                completion=lambda: f"试试 {random.randint(0, len(command_manager.get_commands()))}",
                unmatch_tips=lambda x: f"预期输入为某个命令的id或者名称，而不是 {x}\n例如：/帮助 0",
            ),
        ],
        Option(
            "--page",
            Args["index", int],
            help_text="查看指定页数的命令帮助",
        ),
        Option(
            "--plugin-info",
            alias=["-P", "插件信息"],
            help_text="查看命令所属插件的信息",
            action=store_true,
            default=False,
        ),
        Subcommand(
            "--namespace",
            Args["target?;#指定的命名空间", str],
            Option("--list", help_text="列出所有命名空间", action=store_true, default=False),
            alias=["-N", "命名空间"],
            help_text="是否列出命令所属命名空间",
        ),
        Option("--hide", alias=["-H", "隐藏"], help_text="是否列出隐藏命令", action=store_true, default=False),
        meta=CommandMeta(
            description="显示所有命令帮助",
            usage="可以使用 --hide 参数来显示隐藏命令，使用 -P 参数来显示命令所属插件名称",
            example=f"${plugin_config.nbp_alc_help_text} 1",
        ),
    )

help_matcher = on_alconna(help_cmd, use_cmd_start=True)

for alias in plugin_config.nbp_alc_help_alias:
    help_matcher.shortcut(alias, {"prefix": True, "fuzzy": False})
for alias in plugin_config.nbp_alc_help_all_alias:
    help_matcher.shortcut(alias, {"args": ["--hide"], "prefix": True, "fuzzy": False})

help_matcher.shortcut(
    "(获取)?插件信息", {"args": ["--plugin-info", "{%0}"], "prefix": True, "fuzzy": True, "humanized": "[获取]插件信息"}
)


@help_matcher.handle()
async def help_cmd_handle(arp: Arparma, bot: Bot, event):
    is_plugin_info = arp.query[bool]("plugin-info.value", False)
    is_namespace = arp.query[SubcommandResult]("namespace")
    page = arp.query[int]("page.index", 1)
    target_namespace = is_namespace.args.get("target") if is_namespace else None
    cmds = [
        i
        for i in command_manager.get_commands(target_namespace or "")
        if not i.meta.hide or arp.query[bool]("hide.value", False)
    ]
    cmds = [i for i in cmds if ((mat := referent(i)) and check_supported_adapters(mat, bot)) or not mat]
    if is_namespace and is_namespace.options["list"].value and not target_namespace:
        namespaces = {i.namespace: 0 for i in cmds}
        return await help_matcher.finish(
            "\n".join(
                f" 【{str(index).rjust(len(str(len(namespaces))), '0')}】{n}"
                for index, n in enumerate(namespaces.keys())
            )
        )
    help_names = set()
    for i in cmds:
        help_names.update(i.namespace_config.builtin_option_name["help"])

    footer = lang.require("manager", "help_footer").format(help="|".join(sorted(help_names, key=lambda x: len(x))))
    show_namespace = is_namespace and not is_namespace.options["list"].value and not target_namespace
    if (query := arp.all_matched_args["query"]) != "-1":
        if query.isdigit():
            index = int(query)
            if index < 0 or index >= len(cmds):
                return await help_matcher.finish("查询失败！")
            slot = cmds[index]
        elif not (slot := next((i for i in cmds if query == i.command), None)):
            command_string = "\n".join(
                (
                    f"【{str(index).rjust(len(str(len(cmds))), '0')}】"
                    f"{f'{slot.namespace}::' if show_namespace else ''}{slot.header_display} : "
                    f"{get_info(mat) if is_plugin_info and (mat := referent(slot)) else slot.meta.description}"
                )
                for index, slot in enumerate(cmds)
                if query in str(slot.command)
            )
            if not command_string:
                return await help_matcher.finish("查询失败！")
            return await help_matcher.finish(f"{command_string}\n{footer}")
        _matcher = referent(slot)
        if not _matcher:
            msg = slot.get_help()
        else:
            executor = _matcher.executor
            if is_plugin_info:
                msg = UniMessage.text(get_info(_matcher))
            else:
                msg = await executor.output_converter("help", slot.get_help())
                msg = msg or UniMessage(slot.get_help())
            msg = await executor.send_wrapper(bot, event, msg)
        return await help_matcher.finish(msg)

    if not plugin_config.nbp_alc_page_size:
        header = lang.require("manager", "help_header")
        command_string = "\n".join(
            (
                f" 【{str(index).rjust(len(str(len(cmds))), '0')}】"
                f"{f'{slot.namespace}::' if show_namespace else ''}{slot.header_display} : "
                f"{get_info(mat) if is_plugin_info and (mat := referent(slot)) else slot.meta.description}"
            )
            for index, slot in enumerate(cmds)
        )
        return await help_matcher.finish(f"{header}\n{command_string}\n{footer}")

    max_page = len(cmds) // plugin_config.nbp_alc_page_size + 1
    if page < 1 or page > max_page:
        page = 1
    max_length = plugin_config.nbp_alc_page_size
    footer += "\n" + "输入 '<', 'a' 或 '>', 'd' 来翻页"

    async def _send(_page: int):
        header = (
            lang.require("manager", "help_header")
            + "\t"
            + lang.require("manager", "help_pages").format(current=_page, total=max_page)
        )
        command_string = "\n".join(
            (
                f" 【{str(index).rjust(len(str(_page * max_length)), '0')}】"
                f"{f'{slot.namespace}::' if show_namespace else ''}{slot.header_display} : "
                f"{get_info(mat) if is_plugin_info and (mat := referent(slot)) else slot.meta.description}"
            )
            for index, slot in enumerate(
                cmds[(_page - 1) * max_length : _page * max_length], start=(_page - 1) * max_length
            )
        )
        return await help_matcher.prompt(f"{header}\n{command_string}\n{footer}", timeout=15, block=False)

    while True:
        resp = await _send(page)
        if not resp:
            await help_matcher.finish()
        resp = resp.extract_plain_text().strip().lower()
        if resp in {"a", "<"}:
            page -= 1
            if page < 1:
                page = max_page
        elif resp in {"d", ">"}:
            page += 1
            if page > max_page:
                page = 1
        else:
            help_matcher.skip()
