from base64 import b64decode
from typing import TYPE_CHECKING

from yarl import URL
from nonebot.typing import T_State
from nonebot.internal.adapter import Bot, Event
from nonebot.internal.driver.model import Request

from .uniseg import Image


async def image_fetch(event: Event, bot: Bot, state: T_State, img: Image):
    adapter_name = bot.adapter.get_name()
    if adapter_name == "RedProtocol":
        origin = img.origin
        if TYPE_CHECKING:
            from nonebot.adapters.red.bot import Bot
            from nonebot.adapters.red.message import MediaMessageSegment

            assert isinstance(bot, Bot)
            assert isinstance(origin, MediaMessageSegment)

        return await origin.download(bot)

    if img.url:  # mirai2, qqguild, kook, villa, feishu, minecraft, ding
        req = Request("GET", img.url)
        resp = await bot.adapter.request(req)
        return resp.content
    if not img.id:
        return None
    if adapter_name == "OneBot V11":
        if TYPE_CHECKING:
            from nonebot.adapters.onebot.v11.bot import Bot

            assert isinstance(bot, Bot)
        url = (await bot.get_image(file=img.id))["data"]["url"]
        req = Request("GET", url)
        resp = await bot.adapter.request(req)
        return resp.content
    if adapter_name == "OneBot V12":
        if TYPE_CHECKING:
            from nonebot.adapters.onebot.v12.bot import Bot

            assert isinstance(bot, Bot)
        resp = (await bot.get_file(type="data", file_id=img.id))["data"]
        return b64decode(resp) if isinstance(resp, str) else bytes(resp)
    if adapter_name == "mirai2":
        url = f"https://gchat.qpic.cn/gchatpic_new/0/0-0-" f"{img.id.replace('-', '').upper()}/0"
        req = Request("GET", url)
        resp = await bot.adapter.request(req)
        return resp.content
    if adapter_name == "Telegram":
        if TYPE_CHECKING:
            from nonebot.adapters.telegram.bot import Bot

            assert isinstance(bot, Bot)
        url = URL(bot.bot_config.api_server) / "file" / f"bot{bot.bot_config.token}" / img.id
        req = Request("GET", url)
        resp = await bot.adapter.request(req)
        return resp.content
    if adapter_name == "ntchat":
        raise NotImplementedError("ntchat image fetch not implemented")
