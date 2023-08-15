from typing import TYPE_CHECKING

from nonebot.internal.adapter import Bot, Event
from nonebot.internal.driver.model import Request
from nonebot.typing import T_State
from yarl import URL

from .adapters import Image, Reply


async def reply_handle(event: Event, bot: Bot):
    adapter = bot.adapter
    adapter_name = adapter.get_name()
    if adapter_name == "Telegram":
        if TYPE_CHECKING:
            from nonebot.adapters.telegram.event import MessageEvent

            assert isinstance(event, MessageEvent)
        if event.reply_to_message:
            return Reply(
                event.reply_to_message,
                f"{event.reply_to_message.message_id}.{event.chat.id}",
                event.reply_to_message.original_message,
            )
    elif adapter_name == "Feishu":
        if TYPE_CHECKING:
            from nonebot.adapters.feishu.event import MessageEvent

            assert isinstance(event, MessageEvent)
        if event.reply:
            return Reply(event.reply, event.reply.message_id, event.reply.body.content)
    elif adapter_name == "ntchat":
        if TYPE_CHECKING:
            from nonebot.adapters.ntchat.event import QuoteMessageEvent

            assert isinstance(event, QuoteMessageEvent)
        if event.type == 11061:
            return Reply(event, event.quote_message_id)
    elif adapter_name == "QQ Guild":
        if TYPE_CHECKING:
            from nonebot.adapters.qqguild.event import MessageEvent

            assert isinstance(event, MessageEvent)
        if event.reply:
            return Reply(
                event.reply.message,
                str(event.reply.message.id),
                event.reply.message.content,
            )
    elif adapter_name == "mirai2":
        if TYPE_CHECKING:
            from nonebot.adapters.mirai2.event import MessageEvent

            assert isinstance(event, MessageEvent)
        if event.quote:
            return Reply(event.quote, str(event.quote.id), event.quote.origin)
    elif adapter_name == "Kaiheila":
        if TYPE_CHECKING:
            from nonebot.adapters.kaiheila.event import MessageEvent, ChannelMessageEvent, PrivateMessageEvent
            from nonebot.adapters.kaiheila import Bot as KaiheilaBot

            assert isinstance(event, (MessageEvent, ChannelMessageEvent, PrivateMessageEvent))
            assert isinstance(bot, KaiheilaBot)

        message = await bot.call_api(
            api="directMessage_view"
            if event.get_event_name().startswith("message.private")
            else "message_view",
            msg_id=event.msg_id,
            **(
                {"chat_code": event.event.code}
                if event.get_event_name().startswith("message.private")
                else {}
            ),
        )
        if message.quote:
            return Reply(message.quote, message.quote.id_, None)
    elif adapter_name == "Discord":
        if TYPE_CHECKING:
            from nonebot.adapters.discord import MessageEvent, MessageCreateEvent

            assert isinstance(event, (MessageEvent, MessageCreateEvent))

        if hasattr(event, "message_reference") and hasattr(event.message_reference, "message_id"):  # noqa: E501
            return Reply(event.message_reference, event.message_reference.message_id, None)  # noqa: E501

    elif reply := getattr(event, "reply", None):
        return Reply(reply, str(reply.message_id), getattr(reply, "message", None))
    return None


async def image_fetch(bot: Bot, state: T_State, img: Image):
    if img.url:  # mirai2, qqguild, kook, villa, feishu, minecraft, ding
        req = Request("GET", img.url)
        resp = await bot.adapter.request(req)
        return resp.content
    if not img.id:
        return None
    adapter_name = bot.adapter.get_name()
    if adapter_name == "OneBot V11":
        url = (await bot.get_image(file=img.id))["data"]["url"]
        req = Request("GET", url)
        resp = await bot.adapter.request(req)
        return resp.content
    if adapter_name == "OneBot V12":
        return (await bot.get_file(type="data", file_id=img.id))["data"]
    if adapter_name == "mirai2":
        url = (
            f"https://gchat.qpic.cn/gchatpic_new/0/0-0-"
            f"{img.id.replace('-', '').upper()}/0"
        )
        req = Request("GET", url)
        resp = await bot.adapter.request(req)
        return resp.content
    if adapter_name == "Telegram":
        url = (
                URL(bot.bot_config.api_server)
                / "file"
                / f"bot{bot.bot_config.token}"
                / img.id
        )
        req = Request("GET", url)
        resp = await bot.adapter.request(req)
        return resp.content
    if adapter_name == "ntchat":
        raise NotImplementedError("ntchat image fetch not implemented")
