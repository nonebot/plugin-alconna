import asyncio
from typing import Callable
from typing_extensions import TypeAlias

from nonebot.adapters import Bot
from nonebot.plugin import PluginMetadata

from .segment import At as At
from .rule import at_in as at_in
from .rule import at_me as at_me
from .constraint import log, lang
from .segment import File as File
from .segment import Text as Text
from .target import TARGET_RECORD
from .fallback import AUTO as AUTO
from .params import MsgId as MsgId
from .segment import AtAll as AtAll
from .segment import Audio as Audio
from .segment import Emoji as Emoji
from .segment import Hyper as Hyper
from .segment import Image as Image
from .segment import Other as Other
from .segment import Reply as Reply
from .segment import Video as Video
from .segment import Voice as Voice
from .params import UniMsg as UniMsg
from .target import SCOPES as SCOPES
from .target import Target as Target
from .segment import Button as Button
from .tools import get_bot as get_bot
from .fallback import FORBID as FORBID
from .fallback import IGNORE as IGNORE
from .message import Receipt as Receipt
from .segment import RefNode as RefNode
from .segment import Segment as Segment
from .fallback import TO_TEXT as TO_TEXT
from .segment import Keyboard as Keyboard
from .fallback import ROLLBACK as ROLLBACK
from .params import MessageId as MessageId
from .params import MsgTarget as MsgTarget
from .segment import Reference as Reference
from .message import UniMessage as UniMessage
from .segment import CustomNode as CustomNode
from .tools import image_fetch as image_fetch
from .tools import reply_fetch as reply_fetch
from .params import MessageTarget as MessageTarget
from .constraint import SupportScope as SupportScope
from .segment import custom_handler as custom_handler
from .segment import custom_register as custom_register
from .constraint import SupportAdapter as SupportAdapter
from .fallback import FallbackMessage as FallbackMessage
from .fallback import FallbackSegment as FallbackSegment
from .params import UniversalMessage as UniversalMessage
from .params import UniversalSegment as UniversalSegment
from .constraint import SerializeFailed as SerializeFailed
from .fallback import FallbackStrategy as FallbackStrategy
from .segment import apply_media_to_url as apply_media_to_url
from .constraint import SupportAdapterModule as SupportAdapterModule
from .adapters import alter_get_builder, alter_get_fetcher, alter_get_exporter

__version__ = "0.56.2"

__plugin_meta__ = PluginMetadata(
    name="Universal Segment 插件",
    description="提供抽象的消息元素，与跨平台接收/发送消息功能的库",
    usage="unimsg: UniMsg",
    homepage="https://github.com/nonebot/plugin-alconna/tree/master/src/nonebot_plugin_alconna/uniseg",
    type="library",
    supported_adapters=set(SupportAdapterModule.__members__.values()),
    extra={
        "author": "RF-Tar-Railt",
        "priority": 1,
        "version": __version__,
    },
)


_Dispose: TypeAlias = Callable[[], None]
"""patch 方法的复原函数类型"""


def patch_saa() -> _Dispose:
    from .utils.saa import patch

    return patch()


def patch_matcher_send() -> _Dispose:
    from .utils.matcher import patch

    return patch()


def apply_filehost() -> _Dispose:
    from .utils.filehost import apply

    return apply()


reply_handle = reply_fetch  # backward compatibility

_enable_fetch_targets = False
FETCH_LOCK = asyncio.Lock()


def _register_hook():
    from nonebot import get_driver

    driver = get_driver()

    @driver.on_bot_connect
    async def _(bot: Bot):
        log("DEBUG", f"cache or refresh targets for bot:{bot.self_id}")
        async with FETCH_LOCK:
            await _refresh_bot(bot)

    @driver.on_bot_disconnect
    async def _(bot: Bot):
        async with FETCH_LOCK:
            TARGET_RECORD.pop(bot.self_id, None)
            if fn := alter_get_fetcher(bot.adapter.get_name()):
                fn.cache.pop(bot.self_id, None)


def apply_fetch_targets():
    global _enable_fetch_targets  # noqa: PLW0603

    if _enable_fetch_targets:
        return

    _register_hook()
    _enable_fetch_targets = True


async def _refresh_bot(bot: Bot):
    TARGET_RECORD.pop(bot.self_id, None)
    if not (fn := alter_get_fetcher(bot.adapter.get_name())):
        log("WARNING", lang.require("nbp-uniseg", "unsupported").format(adapter=bot.adapter.get_name()))
        return
    try:
        await fn.refresh(bot)
    except Exception as e:
        log("ERROR", f"bot:{bot} fetch targets failed: {e}")
    TARGET_RECORD[bot.self_id] = fn.get_selector(bot)


def get_fetcher(bot: Bot):
    if not (fn := alter_get_fetcher(bot.adapter.get_name())):
        log("WARNING", lang.require("nbp-uniseg", "unsupported").format(adapter=bot.adapter.get_name()))
        return None
    return fn


def get_builder(bot: Bot):
    if not (fn := alter_get_builder(bot.adapter.get_name())):
        log("WARNING", lang.require("nbp-uniseg", "unsupported").format(adapter=bot.adapter.get_name()))
        return None
    return fn


def get_exporter(bot: Bot):
    if not (fn := alter_get_exporter(bot.adapter.get_name())):
        log("WARNING", lang.require("nbp-uniseg", "unsupported").format(adapter=bot.adapter.get_name()))
        return None
    return fn
