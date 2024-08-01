from typing import Any, Union

from nonebot.matcher import Matcher
from nonebot.adapters import Message, MessageSegment, MessageTemplate
from nonebot.internal.matcher import current_bot, current_event, current_matcher

from nonebot_plugin_alconna.uniseg.message import UniMessage, FallbackStrategy


async def send(
    cls,
    message: Union[str, Message, MessageSegment, MessageTemplate],
    **kwargs: Any,
):
    """发送一条消息给当前交互用户

    参数:
        message: 消息内容
        kwargs: {ref}`nonebot.adapters.Bot.send` 的参数，
            请参考对应 adapter 的 bot 对象 api
    """
    bot = current_bot.get()
    event = current_event.get()
    state = current_matcher.get().state
    if isinstance(message, MessageTemplate):
        _message = message.format(**state)
    else:
        _message = message
    if isinstance(_message, Message):
        _unimsg = UniMessage.generate_sync(message=_message, bot=bot)
    elif isinstance(_message, MessageSegment):
        _unimsg = UniMessage.generate_sync(message=_message.get_message_class()(_message), bot=bot)
    else:
        _unimsg = UniMessage.text(_message)
    _send = await _unimsg.export(bot=bot, fallback=FallbackStrategy.to_text)
    return await bot.send(event=event, message=_send, **kwargs)


_OLD_SEND = Matcher.send


def patch():

    Matcher.send = classmethod(send)  # type: ignore

    def dispose():
        Matcher.send = classmethod(_OLD_SEND)  # type: ignore

    return dispose
