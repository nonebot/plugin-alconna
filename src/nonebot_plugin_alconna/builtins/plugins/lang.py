from arclet.alconna import Alconna, Args, CommandMeta, Field, Option, namespace
from nonebot.plugin import PluginMetadata

from nonebot_plugin_alconna import Match, UniMessage, __supported_adapters__, on_alconna
from nonebot_plugin_alconna.i18n import Lang, lang

__plugin_meta__ = PluginMetadata(
    name="lang",
    description=Lang.nbp_alc_builtin.lang.help.main.cast(),
    usage="/lang list/switch [lang]",
    type="application",
    homepage="https://github.com/nonebot/plugin-alconna/blob/master/src/nonebot_plugin_alconna/builtins/plugins/lang.py",
    config=None,
    supported_adapters=__supported_adapters__,
)

with namespace("builtin/lang") as ns:
    ns.disable_builtin_options = {"shortcut", "completion"}

    cmd = on_alconna(
        Alconna(
            "lang",
            Option("list", Args["name?", str], help_text=Lang.nbp_alc_builtin.lang.help.list.cast()),
            Option(
                "switch",
                Args["locale?", str, Field(completion=lambda: list(lang.locales))],
                help_text=Lang.nbp_alc_builtin.lang.help.switch.cast(),
            ),
            meta=CommandMeta(Lang.nbp_alc_builtin.lang.help.main.cast(), compact=True),
        ),
        use_cmd_start=True,
    )


@cmd.assign("list")
async def _(name: Match[str]):
    try:
        locales = lang.locales_in(name.result) if name.available else lang.locales
    except KeyError:
        await cmd.finish(UniMessage.i18n(Lang.nbp_alc_builtin.lang.config_name_error, name=name.result))
    else:
        await cmd.finish(Lang.nbp_alc_builtin.lang.list() + "\n" + "\n".join(f" * {locale}" for locale in locales))


@cmd.assign("switch")
async def _(locale: Match[str]):
    if not locale.available:
        resp = await cmd.prompt(UniMessage.i18n(Lang.nbp_alc_builtin.lang.locale_missing), timeout=30)
        if resp is None:
            await UniMessage.i18n(Lang.nbp_alc_builtin.lang.locale_timeout).finish()
        _locale = str(resp)
    else:
        _locale = locale.result
    try:
        lang.select(_locale)
    except ValueError as e:
        await cmd.finish(str(e))
    else:
        await UniMessage.i18n(Lang.nbp_alc_builtin.lang.switch, locale=_locale).finish()
