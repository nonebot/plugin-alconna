from typing import TYPE_CHECKING

from nonebot.adapters import Bot, Event
from nonebot.adapters.mail.event import NewMailMessageEvent
from nonebot.adapters.mail.message import Html, Attachment, MessageSegment

from nonebot_plugin_alconna.uniseg.constraint import SupportAdapter
from nonebot_plugin_alconna.uniseg.builder import MessageBuilder, build
from nonebot_plugin_alconna.uniseg.segment import File, Text, Audio, Image, Reply, Video


class MailMessageBuilder(MessageBuilder[MessageSegment]):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.mail

    @build("html")
    def html(self, seg: Html):
        return Text(seg.data["html"]).mark(0, len(seg.data["html"]), "html")

    @build("attachment")
    def attachment(self, seg: Attachment):
        mtype = seg.data["content_type"]
        if mtype and mtype.startswith("image"):
            return Image(
                raw=seg.data["data"],
                mimetype=mtype,
                name=seg.data["name"],
            )
        if mtype and mtype.startswith("audio"):
            return Audio(
                raw=seg.data["data"],
                mimetype=mtype,
                name=seg.data["name"],
            )
        if mtype and mtype.startswith("video"):
            return Video(
                raw=seg.data["data"],
                mimetype=mtype,
                name=seg.data["name"],
            )
        return File(
            raw=seg.data["data"],
            mimetype=seg.data["content_type"],
            name=seg.data["name"],
        )

    async def extract_reply(self, event: Event, bot: Bot):
        if TYPE_CHECKING:
            assert isinstance(event, NewMailMessageEvent)

        if event.reply:
            return Reply(event.reply.id, msg=event.reply.message, origin=event.reply)
        return None
