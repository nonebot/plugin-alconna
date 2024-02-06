from io import BytesIO
from typing import Any

from nonebot import require
from nonebot.internal.matcher import current_bot, current_event

from nonebot_plugin_alconna.uniseg.message import Receipt, UniMessage

try:
    require("nonebot_plugin_saa")
    from nonebot_plugin_saa.registries import MessageId
    from nonebot_plugin_saa import MessageFactory, extract_target
    from nonebot_plugin_saa.registries import Receipt as SaaReceipt
    from nonebot_plugin_saa.utils.exceptions import AdapterNotSupported
    from nonebot_plugin_saa.types.common_message_segment import Text, Image, Reply, Mention
except ImportError:
    raise ImportError("You need to install nonebot_plugin_saa to use this module.")


def convert(mf: MessageFactory) -> UniMessage:
    msg = UniMessage()
    for msf in mf:
        if isinstance(msf, Text):
            msg.text(msf.data["text"])
        elif isinstance(msf, Image):
            image = msf.data["image"]
            if isinstance(image, str):
                msg.image(url=image, name=msf.data["name"])
            elif isinstance(image, (bytes, BytesIO)):
                msg.image(raw=image, name=msf.data["name"])
            else:
                msg.image(path=image, name=msf.data["name"])
        elif isinstance(msf, Reply):
            msg.text(f"[回复:{msf.data['message_id'].dict()}]")
        elif isinstance(msf, Mention):
            user_id = msf.data["user_id"]
            if user_id == "all":
                msg.at_all()
            elif user_id == "here":
                msg.at_all(online=True)
            else:
                msg.at(user_id)
        else:
            msg.text(f"[未知:{msf}]")
    return msg


class UnisegMessageId(MessageId):
    adapter_name: str
    message_id: Any

    class Config:
        arbitrary_types_allowed = True


class UnisegReceipt(SaaReceipt):
    adapter_name: str
    data: Receipt

    async def revoke(self):
        return await self.data.recall()

    class Config:
        arbitrary_types_allowed = True

    @property
    def raw(self) -> Receipt:
        return self.data

    def extract_message_id(self):
        return UnisegMessageId(adapter_name=self.adapter_name, message_id=self.data.msg_ids[0])


async def send(self: MessageFactory, *, at_sender=False, reply=False) -> "SaaReceipt":
    """回复消息，仅能用在事件响应器中"""
    try:
        event = current_event.get()
        bot = current_bot.get()
    except LookupError as e:
        raise RuntimeError("send() 仅能在事件响应器中使用，主动发送消息请使用 send_to") from e
    try:
        target = extract_target(event, bot)
        return await self._do_send(bot, target, event, at_sender, reply)
    except (RuntimeError, AdapterNotSupported):
        receipt = await convert(self).send(target=event, bot=bot, at_sender=at_sender, reply_to=reply)
        return UnisegReceipt(bot_id=receipt.bot.self_id, adapter_name=receipt.exporter.get_adapter(), data=receipt)


MessageFactory.send = send
