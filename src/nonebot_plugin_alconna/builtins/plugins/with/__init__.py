import json
import asyncio
import datetime

from arclet.alconna import namespace
from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata

from nonebot_plugin_alconna import Match, Command, MsgTarget, add_global_extension, __supported_adapters__

from .config import Config
from .extension import PrefixAppendExtension

__plugin_meta__ = PluginMetadata(
    name="with",
    description="设置局部命令前缀",
    usage="/with <name>",
    type="application",
    homepage="https://github.com/nonebot/plugin-alconna/blob/master/src/nonebot_plugin_alconna/builtins/plugins/with",
    config=Config,
    supported_adapters=__supported_adapters__,
)


plugin_config = get_plugin_config(Config)

data = {}


def remove(key: str):
    data.pop(key, None)


with namespace("builtin/with") as ns:
    ns.disable_builtin_options = {"shortcut", "completion"}

    with_ = (
        Command(f"{plugin_config.nbp_alc_with_text} [name:str]", "with 指令")
        .config(compact=True)
        .option("expire", "expire <time:datetime>#设置可能的生效时间")
        .option("unset", "unset #取消当前前缀")
        .usage("设置局部命令前缀")
        .build(use_cmd_start=True, priority=0, block=True)
    )

    for alias in plugin_config.nbp_alc_with_alias:
        with_.shortcut(alias, {"prefix": True, "fuzzy": False})

    @with_.assign("unset")
    async def unset(target: MsgTarget):
        key = json.dumps(target.dump(only_scope=True), ensure_ascii=False)
        if key not in data:
            await with_.finish("当前群组未设置前缀")
        del data[key]
        await with_.finish("取消设置成功")

    @with_.handle()
    async def _(name: Match[str], target: MsgTarget, time: Match[datetime.datetime]):
        key = json.dumps(target.dump(only_scope=True), ensure_ascii=False)
        if not name.available:
            if key not in data:
                await with_.finish("当前群组未设置前缀")
            await with_.finish(f"当前局部前缀为 {data[key]!r}")
        if name.result.startswith(plugin_config.nbp_alc_with_text):
            await with_.finish("无法设置该前缀")
        data[key] = name.result
        if time.available:
            asyncio.get_running_loop().call_later(
                abs((time.result - datetime.datetime.now()).total_seconds()), remove, key  # noqa: DTZ005
            )

        await with_.finish("设置前缀成功")


PrefixAppendExtension.supplier = lambda _, target: data.get(
    json.dumps(target.dump(only_scope=True), ensure_ascii=False)
)
add_global_extension(PrefixAppendExtension)
