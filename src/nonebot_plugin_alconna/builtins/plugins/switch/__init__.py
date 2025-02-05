import random

from tarina import lang
from nonebot.adapters import Bot
from nonebot import get_plugin_config
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata
from arclet.alconna import Args, Field, Option, Alconna, Arparma, CommandMeta, namespace, store_true, command_manager

from nonebot_plugin_alconna import on_alconna, __supported_adapters__

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="switch",
    description="启用或禁用某个命令, 仅限超级用户使用",
    usage="/enable & /disable",
    type="application",
    homepage="https://github.com/nonebot/plugin-alconna/blob/master/src/nonebot_plugin_alconna/builtins/plugins/switch",
    config=Config,
    supported_adapters=__supported_adapters__,
)


plugin_config = get_plugin_config(Config)


with namespace("builtin/switch") as ns:
    ns.disable_builtin_options = {"shortcut"}

    enable_cmd = Alconna(
        plugin_config.nbp_alc_switch_enable,
        Args[
            "query#选择某条命令的id或者名称;/?",
            str,
            Field(
                "-1",
                completion=lambda: f"试试 {random.randint(0, len(command_manager.get_commands()))}",
                unmatch_tips=lambda x: f"预期输入为某个命令的id或者名称，而不是 {x}\n例如：/enable 0",
            ),
        ],
        Option("--hide", alias=["-H", "隐藏"], help_text="是否列出隐藏命令", action=store_true, default=False),
        meta=CommandMeta(
            description="启用某个命令",
            usage="可以使用 --hide 参数来显示隐藏命令",
            example=f"${plugin_config.nbp_alc_switch_enable} 1",
        ),
    )

    disable_cmd = Alconna(
        plugin_config.nbp_alc_switch_disable,
        Args[
            "query#选择某条命令的id或者名称;/?",
            str,
            Field(
                "-1",
                completion=lambda: f"试试 {random.randint(0, len(command_manager.get_commands()))}",
                unmatch_tips=lambda x: f"预期输入为某个命令的id或者名称，而不是 {x}\n例如：/disable 0",
            ),
        ],
        Option(
            "--page",
            Args["index", int],
            help_text="查看指定页数的命令帮助",
        ),
        Option("--hide", alias=["-H", "隐藏"], help_text="是否列出隐藏命令", action=store_true, default=False),
        meta=CommandMeta(
            description="禁用某个命令",
            usage="可以使用 --hide 参数来显示隐藏命令",
            example=f"${plugin_config.nbp_alc_switch_disable} 1",
        ),
    )


enable_matcher = on_alconna(enable_cmd, use_cmd_start=True, permission=SUPERUSER)
disable_matcher = on_alconna(disable_cmd, use_cmd_start=True, permission=SUPERUSER)

for alias in plugin_config.nbp_alc_switch_enable_alias:
    enable_matcher.shortcut(alias, {"prefix": True, "fuzzy": True})

for alias in plugin_config.nbp_alc_switch_disable_alias:
    disable_matcher.shortcut(alias, {"prefix": True, "fuzzy": True})


@enable_matcher.handle()
async def enable_cmd_handle(arp: Arparma, bot: Bot, event):
    is_hide = arp.query[bool]("hide.value", False)
    page = arp.query[int]("page.index", 1)
    cmds = [
        i
        for i in command_manager.get_commands()
        if i not in (enable_cmd, disable_cmd) and (not i.meta.hide or is_hide) and command_manager.is_disable(i)
    ]
    if not cmds:
        return await enable_matcher.finish("没有可用的命令！")
    if (query := arp.all_matched_args["query"]) != "-1":
        if query.isdigit():
            index = int(query)
            if index >= len(cmds) or index < 0:
                return await enable_matcher.finish("查询失败！")
            slot = cmds[index]
            command_manager.set_enabled(slot, enabled=True)
            return await enable_matcher.finish(f"已启用 {slot.header_display}")
        if slot := next((i for i in cmds if query == i.command), None):
            command_manager.set_enabled(slot, enabled=True)
            return await enable_matcher.finish(f"已启用 {slot.header_display}")
        command_string = "\n".join(
            (f"【{str(index).rjust(len(str(len(cmds))), '0')}】{slot.header_display} : {slot.meta.description}")
            for index, slot in enumerate(cmds)
            if query in slot.header_display
        )
        if not command_string:
            return await enable_matcher.finish("查询失败！")
        return await enable_matcher.finish(command_string)
    if not plugin_config.nbp_alc_page_size:
        command_string = "\n".join(
            (f"【{str(index).rjust(len(str(len(cmds))), '0')}】{slot.header_display} : {slot.meta.description}")
            for index, slot in enumerate(cmds)
        )
        return await enable_matcher.finish(command_string)

    max_page = len(cmds) // plugin_config.nbp_alc_page_size + 1
    if page < 1 or page > max_page:
        page = 1
    max_length = plugin_config.nbp_alc_page_size
    footer = "输入 '<', 'a' 或 '>', 'd' 来翻页"

    async def _send(_page: int):
        header = lang.require("manager", "help_pages").format(current=_page, total=max_page)
        command_string = "\n".join(
            (
                f"【{str(index).rjust(len(str(_page * max_length)), '0')}】"
                f"{slot.header_display} :  {slot.meta.description}"
            )
            for index, slot in enumerate(
                cmds[(_page - 1) * max_length : _page * max_length], start=(_page - 1) * max_length
            )
        )
        return await enable_matcher.prompt(f"{header}\n{command_string}\n{footer}", timeout=15, block=False)

    while True:
        resp = await _send(page)
        if not resp:
            await enable_matcher.finish()
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
            enable_matcher.skip()


@disable_matcher.handle()
async def disable_cmd_handle(arp: Arparma, bot: Bot, event):
    is_hide = arp.query[bool]("hide.value", False)
    page = arp.query[int]("page.index", 1)
    cmds = [
        i
        for i in command_manager.get_commands()
        if i not in (enable_cmd, disable_cmd) and (not i.meta.hide or is_hide) and not command_manager.is_disable(i)
    ]
    if not cmds:
        return await disable_matcher.finish("没有可用的命令！")
    if (query := arp.all_matched_args["query"]) != "-1":
        if query.isdigit():
            index = int(query)
            if index >= len(cmds) or index < 0:
                return await disable_matcher.finish("查询失败！")
            slot = cmds[index]
            command_manager.set_enabled(slot, enabled=False)
            return await disable_matcher.finish(f"已禁用 {slot.header_display}")
        if slot := next((i for i in cmds if query == i.command), None):
            command_manager.set_enabled(slot, enabled=False)
            return await disable_matcher.finish(f"已禁用 {slot.header_display}")
        command_string = "\n".join(
            (f"【{str(index).rjust(len(str(len(cmds))), '0')}】{slot.header_display} : {slot.meta.description}")
            for index, slot in enumerate(cmds)
            if query in slot.header_display
        )
        if not command_string:
            return await disable_matcher.finish("查询失败！")
        return await disable_matcher.finish(command_string)
    if not plugin_config.nbp_alc_page_size:
        command_string = "\n".join(
            (f"【{str(index).rjust(len(str(len(cmds))), '0')}】{slot.header_display} : {slot.meta.description}")
            for index, slot in enumerate(cmds)
        )
        return await disable_matcher.finish(command_string)

    max_page = len(cmds) // plugin_config.nbp_alc_page_size + 1
    if page < 1 or page > max_page:
        page = 1
    max_length = plugin_config.nbp_alc_page_size
    footer = "输入 '<', 'a' 或 '>', 'd' 来翻页"

    async def _send(_page: int):
        header = lang.require("manager", "help_pages").format(current=_page, total=max_page)
        command_string = "\n".join(
            (
                f"【{str(index).rjust(len(str(_page * max_length)), '0')}】"
                f"{slot.header_display} :  {slot.meta.description}"
            )
            for index, slot in enumerate(
                cmds[(_page - 1) * max_length : _page * max_length], start=(_page - 1) * max_length
            )
        )
        return await disable_matcher.prompt(f"{header}\n{command_string}\n{footer}", timeout=15, block=False)

    while True:
        resp = await _send(page)
        if not resp:
            await disable_matcher.finish()
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
            disable_matcher.skip()
