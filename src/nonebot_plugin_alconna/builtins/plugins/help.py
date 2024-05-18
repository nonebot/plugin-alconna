import random

from tarina import lang
from nonebot.plugin import PluginMetadata
from arclet.alconna import Args, Field, Option, Alconna, Arparma, CommandMeta, namespace, store_true, command_manager

from nonebot_plugin_alconna import referent, on_alconna

__plugin_meta__ = PluginMetadata(
    name="help",
    description="展示所有命令帮助",
    usage="/help",
    type="application",
    homepage="https://github.com/nonebot/plugin-alconna/blob/master/src/nonebot_plugin_alconna/builtins/plugins/help.py",
    config=None,
    supported_adapters=None,
)

with namespace("builtin/help") as ns:
    ns.disable_builtin_options = {"shortcut"}

    help_cmd = Alconna(
        "help",
        Args[
            "query#选择某条命令的id或者名称查看具体帮助;/?",
            str,
            Field(
                "-1",
                completion=lambda: f"试试 {random.randint(0, len(command_manager.get_commands()))}",
                unmatch_tips=lambda x: f"预期输入为某个命令的id或者名称，而不是 {x}\n例如：/帮助 0",
            ),
        ],
        Option("--hide", help_text="是否列出隐藏命令", action=store_true, default=False),
        meta=CommandMeta(
            description="显示所有命令帮助",
            usage="可以使用 --hide 参数来显示隐藏命令",
            example="$help 1",
        ),
    )

help_matcher = on_alconna(help_cmd, use_cmd_start=True, auto_send_output=True)
help_matcher.shortcut("帮助", {"prefix": True, "fuzzy": False})
help_matcher.shortcut("所有帮助", {"args": ["--hide"], "prefix": True, "fuzzy": False})


@help_matcher.handle()
async def help_cmd_handle(arp: Arparma):
    cmds = [i for i in command_manager.get_commands() if not i.meta.hide or arp.query[bool]("hide.value")]
    if (query := arp.all_matched_args["query"]) != "-1":
        if query.isdigit():
            slot = cmds[int(query)]
            try:
                executor = referent(slot).executor
                msg = await executor.output_converter("help", slot.get_help())
                msg = msg or slot.get_help()
            except Exception:
                msg = slot.get_help()
            return await help_matcher.finish(msg)
        command_string = "\n".join(
            f" [{str(index).rjust(len(str(len(cmds))), '0')}] {slot.header_display} : {slot.meta.description}"
            for index, slot in enumerate(cmds)
            if query in slot.header_display
        )
        if not command_string:
            return await help_matcher.finish("查询失败！")
    else:
        command_string = "\n".join(
            f" [{str(index).rjust(len(str(len(cmds))), '0')}] {slot.header_display} : {slot.meta.description}"
            for index, slot in enumerate(cmds)
        )
    help_names = set()
    for i in cmds:
        help_names.update(i.namespace_config.builtin_option_name["help"])
    header = lang.require("manager", "help_header")
    footer = lang.require("manager", "help_footer").format(help="|".join(sorted(help_names, key=lambda x: len(x))))
    return await help_matcher.finish(f"{header}\n{command_string}\n{footer}")
